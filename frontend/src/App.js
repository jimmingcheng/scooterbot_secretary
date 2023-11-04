import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import HomePage from './HomePage';
import SignUp from './SignUp';
import PrivacyPolicy from './PrivacyPolicy';
import TermsOfService from './TermsOfService';

function App() {
  return (
    <Router>
      <header>
        Scooterbot AI
        <hr/>
      </header>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />
        <Route path="/tos" element={<TermsOfService />} />
      </Routes>
      <footer>
        <hr />
        <ul>
          <li><Link to="/privacy">Privacy</Link></li>
          <li><Link to="/tos">Terms of Service</Link></li>
        </ul>
      </footer>
    </Router>
  );
}

export default App;
