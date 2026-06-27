import { useEffect } from 'react'
import { AppProvider, useApp } from './context/AppContext'
import { Layout } from './components/Layout'

function AppContent() {
  const { loadAgents } = useApp()

  useEffect(() => {
    loadAgents()
  }, [loadAgents])

  return <Layout />
}

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  )
}

export default App
