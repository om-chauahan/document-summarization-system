import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import "./pages/home.css";
import Home from "./pages/Home";
import Upload from "./pages/Upload";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import CustomerSupport from "./pages/CustomerSupport";
import About from "./pages/About";
import Terms from "./pages/Terms";
import Privacy from "./pages/Privacy";
import Profile from "./pages/Profile";
import Settings from "./pages/Settings";
import MyUploads from "./pages/MyUploads";
import Billing from "./pages/Billing";
import Security from "./pages/Security";
import RequireAuth from "./components/RequireAuth";
import OAuthStatus from "./pages/OAuthStatus";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route
          path="/upload"
          element={
            <RequireAuth>
              <Upload />
            </RequireAuth>
          }
        />
        <Route path="/login" element={<Login />} />
        <Route path="/oauth-status" element={<OAuthStatus />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/support" element={<CustomerSupport />} />
        <Route path="/about" element={<About />} />
        <Route
          path="/profile"
          element={
            <RequireAuth>
              <Profile />
            </RequireAuth>
          }
        />
        <Route
          path="/settings"
          element={
            <RequireAuth>
              <Settings />
            </RequireAuth>
          }
        />
        <Route
          path="/my-uploads"
          element={
            <RequireAuth>
              <MyUploads />
            </RequireAuth>
          }
        />
        <Route
          path="/billing"
          element={
            <RequireAuth>
              <Billing />
            </RequireAuth>
          }
        />
        <Route
          path="/security"
          element={
            <RequireAuth>
              <Security />
            </RequireAuth>
          }
        />
        <Route path="/terms" element={<Terms />} />
        <Route path="/privacy" element={<Privacy />} />
      </Routes>
    </Router>
  );
}
