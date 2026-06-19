import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import Comp1 from '../../pure-comp/src/components/Comp1.jsx'
createRoot(document.getElementById('root')).render(
  <Comp1></Comp1>
)
