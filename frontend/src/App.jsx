import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Upload from './pages/Upload.jsx'
import Generation from './pages/Generation.jsx'
import Viewer from './pages/Viewer.jsx'
import History from './pages/History.jsx'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/generate/:packId" element={<Generation />} />
        <Route path="/packs" element={<History />} />
        <Route path="/packs/:packId" element={<Viewer />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
