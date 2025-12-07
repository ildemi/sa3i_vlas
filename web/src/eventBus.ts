// src/eventBus.ts
import mitt from 'mitt'

// Define los tipos de eventos usando el tipo ComponentName
type ComponentName = 'Account' | 'AccountEdit' | 'ChangePassword'

type Events = {
  navigate: ComponentName // Cambia a ComponentName
}

const eventBus = mitt<Events>()

export default eventBus
