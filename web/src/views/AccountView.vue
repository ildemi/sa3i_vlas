<template>
  <main class="main-container">
    <AccountMenu @navigate="handleNavigation" />
    <component :is="currentComponent" />
  </main>
</template>

<script setup lang="ts">
import { shallowRef } from 'vue'
import Account from '@/components/AccountPage.vue'
import AccountEdit from '@/components/AccountEdit.vue'
import AccountMenu from '@/components/AccountMenu.vue'
import ChangePassword from '@/components/ChangePassword.vue'
import eventBus from '@/eventBus'

// Define el tipo de las claves de componentsMap
type ComponentName = 'Account' | 'AccountEdit' | 'ChangePassword'

// Mapa de componentes para asegurar que los nombres coincidan
const componentsMap: Record<ComponentName, typeof Account> = {
  Account,
  AccountEdit,
  ChangePassword
}

// Variable reactiva para controlar el componente actual usando shallowRef
const currentComponent = shallowRef<typeof Account>(componentsMap.Account)

// Función para manejar la navegación
function handleNavigation(componentName: ComponentName) {
  if (componentsMap[componentName]) {
    currentComponent.value = componentsMap[componentName]
  } else {
    console.error(`Component ${componentName} not found in componentsMap`)
  }
}

// Escuchar el evento de navegación
eventBus.on('navigate', handleNavigation)
</script>

<style scoped>
.main-container {
  width: 95%;
  max-width: 1200px;
  margin: 2rem auto;
  padding: 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: flex-start;
  gap: 20px;
}
</style>
