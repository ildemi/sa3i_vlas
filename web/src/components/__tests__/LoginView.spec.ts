import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LoginView from '@/components/LoginPage.vue'

describe('LoginView.vue', () => {
  it('renders login form', () => {
    const wrapper = mount(LoginView)
    expect(wrapper.find('h2').text()).toBe('Login')
  })
})
