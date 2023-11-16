import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import HomePage from './HomePage';
import SignUp from './SignUp';
import PrivacyPolicy from './PrivacyPolicy';
import TermsOfService from './TermsOfService';
import Login from './Login';
import LoginStep4 from './LoginStep4';

function App() {
  return (
    <Router>
      <header>
        <Link to="/">Scooterbot AI</Link>
        <hr/>
      </header>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />
        <Route path="/tos" element={<TermsOfService />} />
        <Route path="/login" element={<Login />} />
        <Route path="/login/step4" element={<LoginStep4 />} />
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
