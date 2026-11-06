import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Home from "./pages/Home.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Search from "./pages/Search.jsx";
import CompareSearch from "./pages/CompareSearch.jsx";
import Explore from "./pages/Explore.jsx";
import CourseDetails from "./pages/CourseDetails.jsx";
import MyLearning from "./pages/MyLearning.jsx";
import Favorites from "./pages/Favorites.jsx";
import KnowledgeGraphPage from "./pages/KnowledgeGraphPage.jsx";
import Evaluation from "./pages/Evaluation.jsx";
import Profile from "./pages/Profile.jsx";
import Login from "./pages/Login.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/search" element={<Search />} />
        <Route path="/compare" element={<CompareSearch />} />
        <Route path="/courses" element={<Explore />} />
        <Route path="/courses/:docId" element={<CourseDetails />} />
        <Route path="/learning" element={<MyLearning />} />
        <Route path="/favorites" element={<Favorites />} />
        <Route path="/knowledge-graph" element={<KnowledgeGraphPage />} />
        <Route path="/evaluation" element={<Evaluation />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
