import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import PromptsPage from './pages/PromptsPage';
import CollectionsPage from './pages/CollectionsPage';
import PromptDetail from './components/PromptDetail';
import Layout from './pages/Layout';
import { CollectionsProvider } from './contexts/CollectionsContext';
import { PromptsProvider } from './contexts/PromptsContext';
import './App.css';

function App() {
  return (
    <PromptsProvider>
    <CollectionsProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<PromptsPage />} />
            <Route path="/collections" element={<CollectionsPage />} />
            <Route path="/prompts/:id" element={<PromptDetail />} />
          </Route>
        </Routes>
      </Router>
    </CollectionsProvider>
    </PromptsProvider>
  );
}

export default App;
