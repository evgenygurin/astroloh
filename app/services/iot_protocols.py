"""IoT protocols implementation for device communication."""

import asyncio
import json
import ssl
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

try:
    import paho.mqtt.client as mqtt

    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logger.warning(
        "MQTT client not available. Install with: pip install paho-mqtt"
    )

import importlib.util

COAP_AVAILABLE = importlib.util.find_spec("aiocoap") is not None
if not COAP_AVAILABLE:
    logger.warning(
        "CoAP client not available. Install with: pip install aiocoap"
    )


class MQTTConnectionPool:
    """Connection pool for MQTT clients."""

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.available_connections: List["MQTTManager"] = []
        self.active_connections: Dict[str, "MQTTManager"] = {}
        self._lock = asyncio.Lock()

    async def get_connection(
        self,
        broker_host: str,
        broker_port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ssl: bool = False,
    ) -> "MQTTManager":
        """Get or create an MQTT connection."""
        connection_key = f"{broker_host}:{broker_port}:{username}:{use_ssl}"

        async with self._lock:
            # Check if we have an active connection
            if connection_key in self.active_connections:
                connection = self.active_connections[connection_key]
                if connection.connected:
                    return connection

            # Try to reuse an available connection
            if self.available_connections:
                connection = self.available_connections.pop()
                connection.reconfigure(
                    broker_host, broker_port, username, password, use_ssl
                )
            else:
                # Create new connection if under limit
                if len(self.active_connections) < self.max_connections:
                    connection = MQTTManager(
                        broker_host, broker_port, username, password, use_ssl
                    )
                else:
                    raise ConnectionError("Maximum MQTT connections reached")

            # Connect and add to active connections
            if await connection.connect():
                self.active_connections[connection_key] = connection
                return connection
            else:
                raise ConnectionError("Failed to connect to MQTT broker")

    async def release_connection(self, connection: "MQTTManager"):
        """Release a connection back to the pool."""
        async with self._lock:
            # Find and remove from active connections
            for key, active_conn in list(self.active_connections.items()):
                if active_conn is connection:
                    del self.active_connections[key]
                    break

            # Add to available connections if under limit
            if len(self.available_connections) < self.max_connections // 2:
                self.available_connections.append(connection)
            else:
                await connection.disconnect()


# Global connection pool instance
mqtt_connection_pool = MQTTConnectionPool()


class MQTTManager:
    """MQTT protocol manager for IoT device communication."""

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ssl: bool = False,
    ):
        if not MQTT_AVAILABLE:
            raise ImportError("MQTT support not available. Install paho-mqtt.")

        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl

        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.subscriptions: Dict[str, Callable] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.connection_retries = 0
        self.max_retries = 3

    def reconfigure(
        self,
        broker_host: str,
        broker_port: int,
        username: Optional[str],
        password: Optional[str],
        use_ssl: bool,
    ):
        """Reconfigure connection parameters for connection reuse."""
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.connected = False

    async def connect(self) -> bool:
        """Connect to MQTT broker."""
        try:
            self.client = mqtt.Client()

            # Set authentication if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)

            # Set SSL if enabled
            if self.use_ssl:
                context = ssl.create_default_context()
                self.client.tls_set_context(context)

            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_publish = self._on_publish

            # Connect to broker
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()

            # Wait for connection
            for _ in range(10):  # Wait up to 10 seconds
                if self.connected:
                    break
                await asyncio.sleep(1)

            if self.connected:
                logger.info(
                    f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}"
                )
                return True
            else:
                logger.error("Failed to connect to MQTT broker")
                return False

        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            return False

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback."""
        if rc == 0:
            self.connected = True
            logger.info("MQTT connection successful")

            # Resubscribe to topics
            for topic in self.subscriptions.keys():
                client.subscribe(topic)

        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback."""
        self.connected = False
        logger.warning("MQTT client disconnected")

    def _on_message(self, client, userdata, msg):
        """MQTT message received callback."""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")

            logger.debug(f"MQTT message received on {topic}: {payload}")

            # Call registered handler
            handler = self.message_handlers.get(topic)
            if handler:
                asyncio.create_task(handler(topic, payload))
            else:
                # Generic handler
                asyncio.create_task(
                    self._handle_generic_message(topic, payload)
                )

        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")

    def _on_publish(self, client, userdata, mid):
        """MQTT publish callback."""
        logger.debug(f"MQTT message {mid} published")

    async def _handle_generic_message(self, topic: str, payload: str):
        """Handle generic MQTT messages."""
        try:
            # Try to parse as JSON
            data = json.loads(payload)

            # Log message for debugging
            logger.info(f"MQTT message on {topic}: {data}")

        except json.JSONDecodeError:
            logger.debug(f"MQTT plain text message on {topic}: {payload}")

    async def subscribe(
        self, topic: str, handler: Optional[Callable] = None
    ) -> bool:
        """Subscribe to MQTT topic."""
        try:
            if not self.connected:
                logger.error("MQTT client not connected")
                return False

            result = self.client.subscribe(topic)

            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.subscriptions[topic] = handler
                if handler:
                    self.message_handlers[topic] = handler

                logger.info(f"Subscribed to MQTT topic: {topic}")
                return True
            else:
                logger.error(f"Failed to subscribe to MQTT topic: {topic}")
                return False

        except Exception as e:
            logger.error(f"MQTT subscription error: {e}")
            return False

    async def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        qos: int = 1,
        retain: bool = False,
    ) -> bool:
        """Publish message to MQTT topic."""
        try:
            if not self.connected:
                logger.error("MQTT client not connected")
                return False

            # Convert payload to JSON
            json_payload = json.dumps(payload)

            result = self.client.publish(
                topic, json_payload, qos=qos, retain=retain
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(
                    f"Published to MQTT topic {topic}: {json_payload}"
                )
                return True
            else:
                logger.error(f"Failed to publish to MQTT topic: {topic}")
                return False

        except Exception as e:
            logger.error(f"MQTT publish error: {e}")
            return False

    async def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.client and self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from MQTT broker")


class HomeKitManager:
    """HomeKit protocol manager for Apple ecosystem devices."""

    def __init__(self):
        self.accessories: Dict[str, Dict[str, Any]] = {}
        self.bridge_info = {
            "name": "Astroloh Smart Home Bridge",
            "manufacturer": "Astroloh",
            "model": "ASH-1",
            "serial": "ASH001",
            "firmware": "1.0.0",
        }

    async def discover_accessories(
        self, timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """Discover HomeKit accessories on the network."""
        try:
            # This would implement Bonjour/mDNS discovery
            # For now, return simulated accessories
            discovered = []

            await asyncio.sleep(1)  # Simulate discovery time

            # Simulated HomeKit devices
            accessories = [
                {
                    "id": "homekit_light_001",
                    "name": "Living Room Light",
                    "type": "lightbulb",
                    "services": ["on", "brightness", "color_temperature"],
                    "manufacturer": "Philips",
                    "model": "Hue White",
                },
                {
                    "id": "homekit_switch_001",
                    "name": "Bedroom Switch",
                    "type": "switch",
                    "services": ["on"],
                    "manufacturer": "Eve",
                    "model": "Smart Switch",
                },
                {
                    "id": "homekit_sensor_001",
                    "name": "Temperature Sensor",
                    "type": "temperature_sensor",
                    "services": ["temperature", "humidity"],
                    "manufacturer": "Aqara",
                    "model": "Temperature Sensor",
                },
            ]

            for accessory in accessories:
                self.accessories[accessory["id"]] = accessory
                discovered.append(accessory)

            logger.info(f"Discovered {len(discovered)} HomeKit accessories")
            return discovered

        except Exception as e:
            logger.error(f"HomeKit discovery error: {e}")
            return []

    async def control_accessory(
        self, accessory_id: str, service: str, value: Any
    ) -> Dict[str, Any]:
        """Control a HomeKit accessory."""
        try:
            accessory = self.accessories.get(accessory_id)
            if not accessory:
                return {"success": False, "error": "Accessory not found"}

            if service not in accessory.get("services", []):
                return {
                    "success": False,
                    "error": f"Service {service} not supported",
                }

            # Simulate control command
            logger.info(
                f"HomeKit: Setting {service} to {value} on {accessory['name']}"
            )

            # In real implementation, this would send HAP commands
            await asyncio.sleep(0.1)

            return {
                "success": True,
                "accessory": accessory["name"],
                "service": service,
                "value": value,
                "response": f"{service} set to {value}",
            }

        except Exception as e:
            logger.error(f"HomeKit control error: {e}")
            return {"success": False, "error": str(e)}

    async def get_accessory_state(self, accessory_id: str) -> Dict[str, Any]:
        """Get current state of a HomeKit accessory."""
        try:
            accessory = self.accessories.get(accessory_id)
            if not accessory:
                return {"success": False, "error": "Accessory not found"}

            # Simulate state reading
            state = {
                "id": accessory_id,
                "name": accessory["name"],
                "type": accessory["type"],
                "online": True,
                "services": {},
            }

            # Add mock service states
            for service in accessory.get("services", []):
                if service == "on":
                    state["services"][service] = True
                elif service == "brightness":
                    state["services"][service] = 75
                elif service == "color_temperature":
                    state["services"][service] = 3000
                elif service == "temperature":
                    state["services"][service] = 22.5
                elif service == "humidity":
                    state["services"][service] = 45

            return {"success": True, "state": state}

        except Exception as e:
            logger.error(f"HomeKit state reading error: {e}")
            return {"success": False, "error": str(e)}


class MatterManager:
    """Matter/Thread protocol manager."""

    def __init__(self):
        self.fabric_id = "astroloh_fabric"
        self.node_id = 1
        self.devices: Dict[str, Dict[str, Any]] = {}

    async def commission_device(
        self, setup_code: str, discriminator: int, device_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Commission a new Matter device."""
        try:
            device_id = f"matter_{discriminator:04d}"

            # Simulate commissioning process
            logger.info(f"Commissioning Matter device {device_id}")

            await asyncio.sleep(2)  # Simulate commissioning time

            device = {
                "id": device_id,
                "name": device_info.get(
                    "name", f"Matter Device {discriminator}"
                ),
                "vendor_id": device_info.get(
                    "vendor_id", 65521
                ),  # Test vendor ID
                "product_id": device_info.get("product_id", 32768),
                "commissioned": True,
                "fabric_id": self.fabric_id,
                "node_id": self.node_id,
                "clusters": device_info.get("clusters", []),
                "endpoints": device_info.get("endpoints", [1]),
            }

            self.devices[device_id] = device
            self.node_id += 1

            return {
                "success": True,
                "device_id": device_id,
                "device": device,
                "message": f"Successfully commissioned {device['name']}",
            }

        except Exception as e:
            logger.error(f"Matter commissioning error: {e}")
            return {"success": False, "error": str(e)}

    async def discover_devices(
        self, timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """Discover Matter devices on the Thread network."""
        try:
            discovered = []

            # Simulate device discovery
            await asyncio.sleep(1)

            # Mock discovered devices
            mock_devices = [
                {
                    "discriminator": 1234,
                    "name": "Smart Bulb",
                    "vendor_id": 4660,  # Philips
                    "product_id": 1,
                    "clusters": [
                        6,
                        8,
                        768,
                    ],  # On/Off, Level Control, Color Control
                    "commissioned": False,
                },
                {
                    "discriminator": 5678,
                    "name": "Smart Plug",
                    "vendor_id": 4631,  # TP-Link
                    "product_id": 2,
                    "clusters": [6],  # On/Off
                    "commissioned": False,
                },
            ]

            for device in mock_devices:
                discovered.append(device)

            logger.info(f"Discovered {len(discovered)} Matter devices")
            return discovered

        except Exception as e:
            logger.error(f"Matter discovery error: {e}")
            return []

    async def send_command(
        self,
        device_id: str,
        cluster_id: int,
        command_id: int,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send Matter command to device."""
        try:
            device = self.devices.get(device_id)
            if not device:
                return {"success": False, "error": "Device not found"}

            if not device.get("commissioned"):
                return {"success": False, "error": "Device not commissioned"}

            if cluster_id not in device.get("clusters", []):
                return {
                    "success": False,
                    "error": f"Cluster {cluster_id} not supported",
                }

            # Simulate command execution
            logger.info(
                f"Matter command to {device['name']}: cluster={cluster_id}, command={command_id}"
            )

            await asyncio.sleep(0.1)

            return {
                "success": True,
                "device": device["name"],
                "cluster_id": cluster_id,
                "command_id": command_id,
                "parameters": parameters,
                "response": "Command executed successfully",
            }

        except Exception as e:
            logger.error(f"Matter command error: {e}")
            return {"success": False, "error": str(e)}

    async def read_attribute(
        self, device_id: str, cluster_id: int, attribute_id: int
    ) -> Dict[str, Any]:
        """Read attribute from Matter device."""
        try:
            device = self.devices.get(device_id)
            if not device:
                return {"success": False, "error": "Device not found"}

            # Simulate attribute reading
            value = None

            # Mock attribute values
            if (
                cluster_id == 6 and attribute_id == 0
            ):  # On/Off cluster, OnOff attribute
                value = True
            elif (
                cluster_id == 8 and attribute_id == 0
            ):  # Level Control cluster, CurrentLevel
                value = 128
            elif (
                cluster_id == 768 and attribute_id == 7
            ):  # Color Control cluster, ColorTemperature
                value = 250

            return {
                "success": True,
                "device": device["name"],
                "cluster_id": cluster_id,
                "attribute_id": attribute_id,
                "value": value,
            }

        except Exception as e:
            logger.error(f"Matter attribute read error: {e}")
            return {"success": False, "error": str(e)}


class IoTProtocolManager:
    """Main IoT protocol manager that coordinates different protocols."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mqtt_manager: Optional[MQTTManager] = None
        self.homekit_manager = HomeKitManager()
        self.matter_manager = MatterManager()
        self.enabled_protocols = set()

    async def initialize(self):
        """Initialize all enabled IoT protocols."""
        try:
            # Initialize MQTT if configured
            mqtt_config = self.config.get("mqtt", {})
            if mqtt_config.get("enabled", False) and MQTT_AVAILABLE:
                self.mqtt_manager = MQTTManager(
                    broker_host=mqtt_config.get("host", "localhost"),
                    broker_port=mqtt_config.get("port", 1883),
                    username=mqtt_config.get("username"),
                    password=mqtt_config.get("password"),
                    use_ssl=mqtt_config.get("ssl", False),
                )

                if await self.mqtt_manager.connect():
                    self.enabled_protocols.add("mqtt")
                    logger.info("MQTT protocol initialized")

            # HomeKit is always available (simulated)
            self.enabled_protocols.add("homekit")
            logger.info("HomeKit protocol initialized")

            # Matter is always available (simulated)
            self.enabled_protocols.add("matter")
            logger.info("Matter protocol initialized")

            logger.info(
                f"Initialized protocols: {', '.join(self.enabled_protocols)}"
            )

        except Exception as e:
            logger.error(f"IoT protocol initialization error: {e}")

    async def send_astrological_update(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        target_devices: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send astrological event updates to IoT devices."""
        try:
            results = {}

            # Prepare update message
            message = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": event_data,
                "source": "astroloh",
            }

            # Send via MQTT
            if "mqtt" in self.enabled_protocols and self.mqtt_manager:
                topic = f"astroloh/events/{event_type}"
                mqtt_result = await self.mqtt_manager.publish(topic, message)
                results["mqtt"] = {"success": mqtt_result, "topic": topic}

            # Send to HomeKit devices
            if "homekit" in self.enabled_protocols:
                homekit_results = []
                if target_devices:
                    for device_id in target_devices:
                        # Convert astrological data to HomeKit actions
                        action = self._convert_to_homekit_action(
                            event_type, event_data
                        )
                        if action:
                            result = (
                                await self.homekit_manager.control_accessory(
                                    device_id,
                                    action["service"],
                                    action["value"],
                                )
                            )
                            homekit_results.append(result)
                results["homekit"] = homekit_results

            # Send to Matter devices
            if "matter" in self.enabled_protocols:
                matter_results = []
                if target_devices:
                    for device_id in target_devices:
                        # Convert astrological data to Matter commands
                        command = self._convert_to_matter_command(
                            event_type, event_data
                        )
                        if command:
                            result = await self.matter_manager.send_command(
                                device_id,
                                command["cluster"],
                                command["command"],
                                command["params"],
                            )
                            matter_results.append(result)
                results["matter"] = matter_results

            return {
                "success": True,
                "event_type": event_type,
                "protocols_used": list(results.keys()),
                "results": results,
            }

        except Exception as e:
            logger.error(f"Failed to send astrological update: {e}")
            return {"success": False, "error": str(e)}

    def _convert_to_homekit_action(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Convert astrological event to HomeKit action."""
        if event_type == "lunar_phase_change":
            phase = event_data.get("phase")
            if phase == "full_moon":
                return {"service": "brightness", "value": 100}
            elif phase == "new_moon":
                return {"service": "brightness", "value": 10}

        elif event_type == "planetary_transit":
            planet = event_data.get("planet")
            if planet == "mars":
                return {
                    "service": "color_temperature",
                    "value": 2000,
                }  # Warm red
            elif planet == "venus":
                return {
                    "service": "color_temperature",
                    "value": 2700,
                }  # Warm pink

        return None

    def _convert_to_matter_command(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Convert astrological event to Matter command."""
        if event_type == "lunar_phase_change":
            phase = event_data.get("phase")
            if phase == "full_moon":
                return {
                    "cluster": 8,
                    "command": 4,
                    "params": {"level": 254},
                }  # Move to level
            elif phase == "new_moon":
                return {
                    "cluster": 8,
                    "command": 4,
                    "params": {"level": 25},
                }  # Move to level

        elif event_type == "planetary_transit":
            # Color control commands
            return {
                "cluster": 768,
                "command": 7,
                "params": {"color_temp": 250},
            }

        return None

    async def setup_astrology_subscriptions(self):
        """Set up MQTT subscriptions for astrological data."""
        if "mqtt" in self.enabled_protocols and self.mqtt_manager:
            # Subscribe to various astrological topics
            await self.mqtt_manager.subscribe(
                "astroloh/lunar_phases/+", self._handle_lunar_phase_message
            )

            await self.mqtt_manager.subscribe(
                "astroloh/transits/+", self._handle_transit_message
            )

            await self.mqtt_manager.subscribe(
                "astroloh/horoscope/+", self._handle_horoscope_message
            )

    async def _handle_lunar_phase_message(self, topic: str, payload: str):
        """Handle lunar phase MQTT messages."""
        try:
            data = json.loads(payload)
            logger.info(f"Lunar phase update: {data}")

            # Process lunar phase change
            # This could trigger automation rules or device updates

        except Exception as e:
            logger.error(f"Error handling lunar phase message: {e}")

    async def _handle_transit_message(self, topic: str, payload: str):
        """Handle planetary transit MQTT messages."""
        try:
            data = json.loads(payload)
            logger.info(f"Transit update: {data}")

            # Process transit information

        except Exception as e:
            logger.error(f"Error handling transit message: {e}")

    async def _handle_horoscope_message(self, topic: str, payload: str):
        """Handle horoscope MQTT messages."""
        try:
            data = json.loads(payload)
            logger.info(f"Horoscope update: {data}")

            # Process horoscope information

        except Exception as e:
            logger.error(f"Error handling horoscope message: {e}")

    async def get_protocol_status(self) -> Dict[str, Any]:
        """Get status of all IoT protocols."""
        status = {}

        # MQTT status
        if self.mqtt_manager:
            status["mqtt"] = {
                "enabled": True,
                "connected": self.mqtt_manager.connected,
                "broker": f"{self.mqtt_manager.broker_host}:{self.mqtt_manager.broker_port}",
                "subscriptions": len(self.mqtt_manager.subscriptions),
            }
        else:
            status["mqtt"] = {"enabled": False}

        # HomeKit status
        status["homekit"] = {
            "enabled": True,
            "accessories": len(self.homekit_manager.accessories),
        }

        # Matter status
        status["matter"] = {
            "enabled": True,
            "devices": len(self.matter_manager.devices),
            "fabric_id": self.matter_manager.fabric_id,
        }

        return status

    async def shutdown(self):
        """Shutdown all IoT protocol managers."""
        if self.mqtt_manager:
            await self.mqtt_manager.disconnect()

        logger.info("IoT protocol managers shut down")
