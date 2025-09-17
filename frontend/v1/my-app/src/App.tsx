import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import DayView from "@/pages/DayView";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DayView />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

