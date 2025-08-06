"""IoT device management service."""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.iot_models import (
    IoTDevice,
    DeviceType,
    DeviceStatus,
    DeviceCommand,
    IoTDeviceCreate,
    IoTDeviceUpdate,
)
from app.services.encryption import EncryptionService
from app.services.cache_service import cache_service


class IoTDeviceManager:
    """Manages IoT devices and their state."""

    def __init__(self, db: AsyncSession, encryption_service: EncryptionService):
        self.db = db
        self.encryption_service = encryption_service
        self.device_connections: Dict[str, Any] = {}
        self.command_queue: asyncio.Queue = asyncio.Queue()

    async def register_device(
        self, user_id: int, device_data: IoTDeviceCreate
    ) -> IoTDevice:
        """Register a new IoT device."""
        try:
            # Encrypt sensitive device configuration
            encrypted_config = None
            if device_data.configuration:
                config_json = json.dumps(device_data.configuration)
                encrypted_config = await self.encryption_service.encrypt_data(
                    config_json
                )

            device = IoTDevice(
                user_id=user_id,
                device_id=device_data.device_id,
                name=device_data.name,
                device_type=device_data.device_type.value,
                protocol=device_data.protocol.value,
                manufacturer=device_data.manufacturer,
                model=device_data.model,
                capabilities=device_data.capabilities,
                configuration=encrypted_config,
                location=device_data.location,
                room=device_data.room,
                status=DeviceStatus.PAIRING.value,
            )

            self.db.add(device)
            await self.db.commit()
            await self.db.refresh(device)

            # Invalidate user devices cache
            await cache_service.invalidate_user_devices(user_id)
            
            logger.info(f"Registered IoT device: {device.name} ({device.device_id})")
            return device

        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            await self.db.rollback()
            raise

    async def get_user_devices(
        self, user_id: int, device_type: Optional[DeviceType] = None
    ) -> List[IoTDevice]:
        """Get all devices for a user."""
        try:
            # Try cache first (only for requests without type filter for simplicity)
            if not device_type:
                cached_devices = await cache_service.get_user_devices(user_id)
                if cached_devices is not None:
                    logger.debug(f"Retrieved {len(cached_devices)} devices from cache for user {user_id}")
                    return [IoTDevice(**device_data) for device_data in cached_devices]
            
            query = select(IoTDevice).where(IoTDevice.user_id == user_id)
            
            if device_type:
                query = query.where(IoTDevice.device_type == device_type.value)

            result = await self.db.execute(query)
            devices = result.scalars().all()

            # Decrypt configurations for response
            device_list = []
            for device in devices:
                if device.configuration:
                    try:
                        decrypted_config = await self.encryption_service.decrypt_data(
                            device.configuration
                        )
                        device.configuration = json.loads(decrypted_config)
                    except Exception as e:
                        logger.warning(f"Failed to decrypt device config: {e}")
                        device.configuration = {}
                
                device_list.append(device)

            # Cache the result if no type filter
            if not device_type and device_list:
                device_data_list = [
                    {
                        'id': d.id,
                        'user_id': d.user_id,
                        'device_id': d.device_id,
                        'name': d.name,
                        'device_type': d.device_type,
                        'protocol': d.protocol,
                        'manufacturer': d.manufacturer,
                        'model': d.model,
                        'status': d.status,
                        'capabilities': d.capabilities,
                        'configuration': d.configuration,
                        'location': d.location,
                        'room': d.room,
                        'last_seen': d.last_seen.isoformat() if d.last_seen else None,
                        'created_at': d.created_at.isoformat() if d.created_at else None,
                    }
                    for d in device_list
                ]
                await cache_service.set_user_devices(user_id, device_data_list)
                logger.debug(f"Cached {len(device_list)} devices for user {user_id}")

            return device_list

        except Exception as e:
            logger.error(f"Failed to get user devices: {e}")
            return []

    async def update_device(
        self, device_id: int, user_id: int, update_data: IoTDeviceUpdate
    ) -> Optional[IoTDevice]:
        """Update device information."""
        try:
            query = select(IoTDevice).where(
                and_(IoTDevice.id == device_id, IoTDevice.user_id == user_id)
            )
            result = await self.db.execute(query)
            device = result.scalar_one_or_none()

            if not device:
                return None

            # Update fields
            if update_data.name:
                device.name = update_data.name
            if update_data.status:
                device.status = update_data.status.value
            if update_data.location:
                device.location = update_data.location
            if update_data.room:
                device.room = update_data.room

            # Encrypt and update configuration
            if update_data.configuration:
                config_json = json.dumps(update_data.configuration)
                encrypted_config = await self.encryption_service.encrypt_data(
                    config_json
                )
                device.configuration = encrypted_config

            device.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(device)

            # Invalidate user devices cache
            await cache_service.invalidate_user_devices(user_id)

            logger.info(f"Updated device: {device.name}")
            return device

        except Exception as e:
            logger.error(f"Failed to update device: {e}")
            await self.db.rollback()
            return None

    async def send_command(
        self, device_id: str, command: DeviceCommand, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Send command to IoT device."""
        try:
            # Find device and verify user ownership if user_id provided
            if user_id:
                query = select(IoTDevice).where(
                    and_(IoTDevice.device_id == device_id, IoTDevice.user_id == user_id)
                )
            else:
                query = select(IoTDevice).where(IoTDevice.device_id == device_id)
            
            result = await self.db.execute(query)
            device = result.scalar_one_or_none()

            if not device:
                error_msg = "Device not found" if not user_id else "Device not found or access denied"
                raise PermissionError(error_msg)

            if device.status != DeviceStatus.ONLINE.value:
                return {"success": False, "error": "Device offline"}

            # Route command based on device protocol
            response = await self._route_command(device, command)
            
            # Update last seen
            device.last_seen = datetime.utcnow()
            await self.db.commit()

            return response

        except Exception as e:
            logger.error(f"Failed to send command to device {device_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _route_command(
        self, device: IoTDevice, command: DeviceCommand
    ) -> Dict[str, Any]:
        """Route command to appropriate protocol handler."""
        protocol_handlers = {
            "matter": self._handle_matter_command,
            "homekit": self._handle_homekit_command,
            "mqtt": self._handle_mqtt_command,
            "google_assistant": self._handle_google_assistant_command,
            "alexa": self._handle_alexa_command,
        }

        handler = protocol_handlers.get(device.protocol)
        if not handler:
            return {"success": False, "error": f"Unsupported protocol: {device.protocol}"}

        return await handler(device, command)

    async def _handle_matter_command(
        self, device: IoTDevice, command: DeviceCommand
    ) -> Dict[str, Any]:
        """Handle Matter/Thread protocol commands."""
        # Implementation would connect to Matter controller
        logger.info(f"Matter command {command.command} to {device.device_id}")
        
        # Simulate command execution
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "protocol": "matter",
            "command": command.command,
            "response": f"Command {command.command} executed on {device.name}",
        }

    async def _handle_homekit_command(
        self, device: IoTDevice, command: DeviceCommand
    ) -> Dict[str, Any]:
        """Handle HomeKit protocol commands."""
        # Implementation would connect to HomeKit accessory
        logger.info(f"HomeKit command {command.command} to {device.device_id}")
        
        # Simulate command execution
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "protocol": "homekit",
            "command": command.command,
            "response": f"Command {command.command} executed on {device.name}",
        }

    async def _handle_mqtt_command(
        self, device: IoTDevice, command: DeviceCommand
    ) -> Dict[str, Any]:
        """Handle MQTT protocol commands."""
        # Implementation would publish to MQTT broker
        logger.info(f"MQTT command {command.command} to {device.device_id}")
        
        # Simulate MQTT publish
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "protocol": "mqtt",
            "command": command.command,
            "response": f"MQTT message published to {device.name}",
        }

    async def _handle_google_assistant_command(
        self, device: IoTDevice, command: DeviceCommand
    ) -> Dict[str, Any]:
        """Handle Google Assistant integration commands."""
        logger.info(f"Google Assistant command {command.command} to {device.device_id}")
        
        # Implementation would use Google Smart Home API
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "protocol": "google_assistant",
            "command": command.command,
            "response": f"Google Assistant command executed on {device.name}",
        }

    async def _handle_alexa_command(
        self, device: IoTDevice, command: DeviceCommand
    ) -> Dict[str, Any]:
        """Handle Amazon Alexa integration commands."""
        logger.info(f"Alexa command {command.command} to {device.device_id}")
        
        # Implementation would use Alexa Smart Home API
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "protocol": "alexa",
            "command": command.command,
            "response": f"Alexa command executed on {device.name}",
        }

    async def update_device_status(self, device_id: str, status: DeviceStatus) -> bool:
        """Update device online/offline status."""
        try:
            query = select(IoTDevice).where(IoTDevice.device_id == device_id)
            result = await self.db.execute(query)
            device = result.scalar_one_or_none()

            if device:
                device.status = status.value
                device.last_seen = datetime.utcnow()
                await self.db.commit()
                
                logger.info(f"Device {device.name} status updated to {status.value}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update device status: {e}")
            return False

    async def get_device_capabilities(self, device_id: str) -> Dict[str, Any]:
        """Get device capabilities and current state."""
        try:
            query = select(IoTDevice).where(IoTDevice.device_id == device_id)
            result = await self.db.execute(query)
            device = result.scalar_one_or_none()

            if not device:
                return {}

            capabilities = device.capabilities or {}
            
            # Add runtime information
            capabilities.update({
                "status": device.status,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                "location": device.location,
                "room": device.room,
            })

            return capabilities

        except Exception as e:
            logger.error(f"Failed to get device capabilities: {e}")
            return {}

    async def discover_devices(self, protocol: str, timeout: int = 30) -> List[Dict[str, Any]]:
        """Discover available devices on the network."""
        discovered = []
        
        try:
            # Different discovery methods based on protocol
            if protocol == "matter":
                discovered = await self._discover_matter_devices(timeout)
            elif protocol == "homekit":
                discovered = await self._discover_homekit_devices(timeout)
            elif protocol == "mqtt":
                discovered = await self._discover_mqtt_devices(timeout)
            
            logger.info(f"Discovered {len(discovered)} {protocol} devices")
            return discovered

        except Exception as e:
            logger.error(f"Device discovery failed for {protocol}: {e}")
            return []

    async def _discover_matter_devices(self, timeout: int) -> List[Dict[str, Any]]:
        """Discover Matter devices."""
        # Simulate device discovery
        await asyncio.sleep(1)
        return [
            {
                "device_id": "matter_light_001",
                "name": "Smart Bulb Living Room",
                "device_type": "smart_light",
                "manufacturer": "Philips",
                "model": "Hue Bulb",
                "capabilities": ["on_off", "brightness", "color"],
            }
        ]

    async def _discover_homekit_devices(self, timeout: int) -> List[Dict[str, Any]]:
        """Discover HomeKit devices."""
        # Simulate device discovery
        await asyncio.sleep(1)
        return [
            {
                "device_id": "homekit_switch_001",
                "name": "Smart Switch Bedroom",
                "device_type": "smart_plug",
                "manufacturer": "Eve",
                "model": "Smart Switch",
                "capabilities": ["on_off", "power_monitoring"],
            }
        ]

    async def _discover_mqtt_devices(self, timeout: int) -> List[Dict[str, Any]]:
        """Discover MQTT devices."""
        # Simulate device discovery
        await asyncio.sleep(1)
        return [
            {
                "device_id": "mqtt_sensor_001", 
                "name": "Temperature Sensor",
                "device_type": "sensor",
                "manufacturer": "Generic",
                "model": "DHT22",
                "capabilities": ["temperature", "humidity"],
            }
        ]