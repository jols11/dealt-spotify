import { formatNumber } from './cn'
import { describe, expect, it } from 'vitest'

describe('formatNumber', () => {
  it('formats thousands', () => {
    expect(formatNumber(12438)).toBe('12,438')
  })
  it('handles empty values', () => {
    expect(formatNumber(null)).toBe('—')
  })
})
