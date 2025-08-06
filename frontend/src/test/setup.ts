import '@testing-library/jest-dom'
import { afterEach, expect } from 'vitest'
import { cleanup } from '@testing-library/react'

// Extend Vitest's expect with jest-dom matchers  
expect.extend({})

// Cleanup after each test case (e.g. clearing jsdom)
afterEach(() => {
  cleanup()
})