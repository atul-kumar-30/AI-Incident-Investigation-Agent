import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import IncidentList from './pages/IncidentList';
import CreateIncident from './pages/CreateIncident';
import IncidentDetail from './pages/IncidentDetail';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="incidents" element={<IncidentList />} />
          <Route path="incidents/new" element={<CreateIncident />} />
          <Route path="incidents/:id" element={<IncidentDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
