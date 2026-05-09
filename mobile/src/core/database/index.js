import { Database } from '@nozbe/watermelondb'
import SQLiteAdapter from '@nozbe/watermelondb/adapters/sqlite'
import { mySchema } from './schema'

// DÉCISION CTO : Adaptateur SQLite local "Offline-First".
// Permet de stocker les tickets et validations sans aucune connexion internet.
// Si le réseau tombe, le bus/métro continue de fonctionner à 100%.
const adapter = new SQLiteAdapter({
  schema: mySchema,
  dbName: 'sitp_offline_db',
  jsi: true, // Interface synchrone ultra-rapide React Native
})

export const database = new Database({
  adapter,
  modelClasses: [
    // L'injection des modèles se fait ici
  ],
})
