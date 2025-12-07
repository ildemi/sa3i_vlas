<template>
  <div class="sidebar">
    <button @click="navigateTo('Account')" class="menu-button">View Profile</button>
    <button @click="navigateTo('AccountEdit')" class="menu-button">Edit Profile</button>
    <button @click="navigateTo('ChangePassword')" class="menu-button">Change Password</button>
  </div>
</template>

<script setup lang="ts">
import eventBus from '@/eventBus'

// Define el tipo de nombre de componente
type ComponentName = 'Account' | 'AccountEdit' | 'ChangePassword'

const navigateTo = (componentName: ComponentName) => {
  eventBus.emit('navigate', componentName)
}
</script>

<style scoped>
.sidebar {
  width: 250px;
  background-color: white;
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  gap: 1rem;
}

.menu-button {
  background: linear-gradient(45deg, #2196f3, #1976d2);
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 50px;
  cursor: pointer;
  text-align: left;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
}

.menu-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(33, 150, 243, 0.4);
  background: linear-gradient(45deg, #1976d2, #1565c0);
}
</style>
