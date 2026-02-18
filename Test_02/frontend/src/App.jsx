import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './components/Dashboard/Dashboard';

const IdeaBoard = lazy(() => import('./pages/IdeaBoard'));
const LiquidityStress = lazy(() => import('./pages/LiquidityStress'));
const CryptoTrends = lazy(() => import('./pages/CryptoTrends'));
const IntelligenceBoard = lazy(() => import('./pages/IntelligenceBoard'));
const Disclosures = lazy(() => import('./pages/Disclosures'));

const PageLoader = () => (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 'calc(100vh - 56px)', color: '#94a3b8' }}>
        Loading...
    </div>
);

function App() {
    return (
        <Router>
            <Routes>
                <Route element={<Layout />}>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/ideas" element={<Suspense fallback={<PageLoader />}><IdeaBoard /></Suspense>} />
                    <Route path="/liquidity-stress" element={<Suspense fallback={<PageLoader />}><LiquidityStress /></Suspense>} />
                    <Route path="/crypto-trends" element={<Suspense fallback={<PageLoader />}><CryptoTrends /></Suspense>} />
                    <Route path="/intelligence" element={<Suspense fallback={<PageLoader />}><IntelligenceBoard /></Suspense>} />
                    <Route path="/disclosures" element={<Suspense fallback={<PageLoader />}><Disclosures /></Suspense>} />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;
