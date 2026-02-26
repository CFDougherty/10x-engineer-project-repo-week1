import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import PromptsPage from './pages/PromptsPage';
import CollectionsPage from './pages/CollectionsPage';
import PromptDetail from './components/PromptDetail';
import Layout from './pages/Layout';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<PromptsPage />} />
          <Route path="/collections" element={<CollectionsPage />} />
          <Route path="/prompts/:id" element={<PromptDetail />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
