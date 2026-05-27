import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "@/components/Layout";
import PlayerProfilePage from "@/pages/PlayerProfilePage";
import TopMetaPage from "@/pages/TopMetaPage";
import ChampionAnalysisPage from "@/pages/ChampionAnalysisPage";
import ItemAnalysisPage from "@/pages/ItemAnalysisPage";
import GeneralAnalysisPage from "@/pages/GeneralAnalysisPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/players" element={<PlayerProfilePage />} />
          <Route path="/meta" element={<TopMetaPage />} />
          <Route path="/champions" element={<ChampionAnalysisPage />} />
          <Route path="/items" element={<ItemAnalysisPage />} />
          <Route path="/analysis" element={<GeneralAnalysisPage />} />
          <Route path="*" element={<Navigate to="/players" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
