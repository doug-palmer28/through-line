import { Route, Routes } from "react-router-dom";
import { AuthProvider, RequireStaff } from "./auth";
import Layout from "./components/Layout";
import AuthPage from "./pages/AuthPage";
import Dashboard from "./pages/Dashboard";
import Home from "./pages/Home";
import LogicModel from "./pages/LogicModel";
import ParticipantPortal from "./pages/ParticipantPortal";
import Grants from "./pages/Grants";
import ReportDesigner from "./pages/ReportDesigner";
import Usage from "./pages/Usage";
import Tools from "./pages/Tools";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Participants get their own simple portal, separate from staff. */}
        <Route path="participant" element={<ParticipantPortal />} />
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="login" element={<AuthPage mode="login" />} />
          <Route path="signup" element={<AuthPage mode="signup" />} />
          <Route path="logic-model" element={<RequireStaff><LogicModel /></RequireStaff>} />
          <Route path="tools" element={<RequireStaff><Tools /></RequireStaff>} />
          <Route path="dashboard" element={<RequireStaff><Dashboard /></RequireStaff>} />
          <Route path="report" element={<RequireStaff><ReportDesigner /></RequireStaff>} />
          <Route path="grants" element={<RequireStaff><Grants /></RequireStaff>} />
          <Route path="usage" element={<RequireStaff><Usage /></RequireStaff>} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
