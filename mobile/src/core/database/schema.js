import { appSchema, tableSchema } from '@nozbe/watermelondb'

export const mySchema = appSchema({
  version: 1,
  tables: [
    tableSchema({
      name: 'tickets',
      columns: [
        { name: 'remote_id', type: 'string' },
        { name: 'price_paid', type: 'number' },
        { name: 'zone_validity', type: 'string' },
        { name: 'cryptographic_signature', type: 'string' },
        { name: 'valid_from', type: 'number' },
        { name: 'valid_until', type: 'number' },
        { name: 'status', type: 'string' },
        { name: 'created_at', type: 'number' },
      ]
    }),
    tableSchema({
      name: 'validation_logs',
      columns: [
        { name: 'ticket_id', type: 'string' },
        { name: 'scan_location_lat', type: 'number' },
        { name: 'scan_location_lng', type: 'number' },
        { name: 'scanned_at', type: 'number' },
        { name: 'is_cryptographically_valid', type: 'boolean' },
        { name: 'sync_status', type: 'string' } // 'PENDING' ou 'SYNCED'
      ]
    })
  ]
})
