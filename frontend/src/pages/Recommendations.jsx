import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';
import ForceGraph2D from 'react-force-graph-2d';
import { 
  Filter, 
  Activity, 
  CheckCircle, 
  ThumbsDown, 
  PlayCircle,
  Database,
  Search
} from 'lucide-react';

export default function Recommendations() {
  const location = useLocation();
  const userId = location.state?.userId || 1;

  const [recommendations, setRecommendations] = useState([]);
  const [algoLog, setAlgoLog] = useState([]);
  const [algoMessage, setAlgoMessage] = useState("");
  const [networkData, setNetworkData] = useState(null);
  const [loading, setLoading] = useState(true);

  const [domains, setDomains] = useState({});
  const [constraints, setConstraints] = useState({
    user_id: userId,
    k: 10,
    genre: null,
    language: null,
    release_year: null,
    runtime: null
  });

  // Fetch initial domains
  useEffect(() => {
    axios.get('http://127.0.0.1:8000/movies/domains')
      .then(res => setDomains(res.data))
      .catch(err => console.error("Could not fetch domains", err));
  }, []);

  const fetchRecommendations = (payload = null) => {
    setLoading(true);
    if (!payload && !constraints.genre && !constraints.language && !constraints.release_year && !constraints.runtime) {
      // Basic recommendation
      axios.get(`http://127.0.0.1:8000/recommendations?user_id=${constraints.user_id}&k=${constraints.k}`)
        .then(res => {
          setRecommendations(res.data.recommendations);
          setAlgoLog(res.data.log);
          setAlgoMessage(res.data.message);
          setNetworkData(res.data.network_data);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    } else {
      // Constrained recommendation
      const reqPayload = payload || constraints;
      axios.post('http://127.0.0.1:8000/constraints', reqPayload)
        .then(res => {
          setRecommendations(res.data.recommendations);
          setAlgoLog(res.data.log);
          setAlgoMessage(res.data.message);
          setNetworkData(res.data.network_data);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [constraints.user_id]);

  const applyConstraint = (key, value) => {
    const newConstraints = { ...constraints, [key]: value };
    setConstraints(newConstraints);
    fetchRecommendations(newConstraints);
  };

  const handleCritique = (type, value) => {
    let newConstraints = { ...constraints };
    if (type === 'different_genre') {
      newConstraints.genre = value;
    } else if (type === 'newer') {
      newConstraints.release_year = [">=", value];
    } else if (type === 'older') {
      newConstraints.release_year = ["<=", value];
    }
    setConstraints(newConstraints);
    fetchRecommendations(newConstraints);
  };

  const getDynamicCritiques = (movie) => {
    const critiques = [];
    
    // Genre critique
    const movieGenres = movie.genres ? movie.genres.split('|') : [];
    const allGenres = domains.genre || [];
    const otherGenres = allGenres.filter(g => !movieGenres.includes(g));
    if (otherGenres.length > 0) {
      // Deterministically pick a different genre
      const otherGenre = otherGenres[movie.movie_id % otherGenres.length];
      critiques.push({ id: 1, label: `Try ${otherGenre}`, type: 'different_genre', value: otherGenre, icon: ThumbsDown });
    }
    
    // Year critique
    if (movie.release_year) {
      if (movie.release_year < 1990) {
        critiques.push({ id: 2, label: 'More modern (> 1990)', type: 'newer', value: 1990, icon: Activity });
      } else {
        critiques.push({ id: 3, label: 'A classic instead (< 1980)', type: 'older', value: 1980, icon: PlayCircle });
      }
    }
    
    return critiques.slice(0, 2);
  };

  const clearConstraints = () => {
    const fresh = { user_id: userId, k: 10, genre: null, language: null, release_year: null, runtime: null };
    setConstraints(fresh);
    fetchRecommendations(fresh);
  };

  return (
    <div className="container" style={{ padding: '30px 24px', display: 'flex', gap: '30px' }}>
      
      {/* Left Sidebar: Constraints */}
      <div style={{ width: '260px', flexShrink: 0 }}>
        <div className="glass-panel" style={{ padding: '20px', position: 'sticky', top: '100px' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1.1rem', marginBottom: '20px' }}>
            <Filter size={18} /> Hard Filters
          </h3>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.85rem', color: 'var(--text-main)' }}>Genre</label>
            <select 
              className="input-field" 
              value={constraints.genre || ""} 
              onChange={e => applyConstraint('genre', e.target.value || null)}
            >
              <option value="">Any Genre</option>
              {[...(domains.genre || [])].sort().map(g => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.85rem', color: 'var(--text-main)' }}>Language</label>
            <select 
              className="input-field" 
              value={constraints.language || ""} 
              onChange={e => applyConstraint('language', e.target.value || null)}
            >
              <option value="">Any Language</option>
              {[...(domains.language || [])].sort().map(l => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>

          <button onClick={clearConstraints} className="secondary-btn" style={{ width: '100%', fontSize: '0.85rem' }}>
            Reset Filters
          </button>
        </div>
      </div>

      {/* Main Content: Recommendations */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '20px', borderBottom: '1px solid var(--border-color)', paddingBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '1.8rem', margin: '0 0 8px 0' }}>Top Matches</h2>
            <p style={{ color: 'var(--text-main)', margin: 0 }}>Found for User {userId}</p>
          </div>
          <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>
            <Database size={16} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'text-bottom' }} />
            Hybrid Predictor
          </div>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px' }}>
            <Activity className="animate-fade-in" size={40} color="var(--accent-green)" style={{ animation: 'pulse 1.5s infinite' }} />
            <p style={{ marginTop: '16px', color: 'var(--text-main)' }}>Running Naive Bayes & CSP Engine...</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {recommendations.length === 0 ? (
              <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>
                <Search size={40} color="var(--border-color)" style={{ marginBottom: '16px' }} />
                <h3>No Matches Found</h3>
                <p style={{ color: 'var(--text-main)' }}>Try relaxing your constraints or letting the backtracker decide.</p>
              </div>
            ) : recommendations.map((rec, idx) => (
              <div key={rec.movie_id} className="glass-panel animate-fade-in" style={{ display: 'flex', padding: '20px', gap: '20px', animationDelay: `${idx * 0.05}s` }}>
                <div style={{ width: '120px', height: '180px', background: 'var(--bg-color-alt)', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, border: '1px solid var(--glass-border)', textAlign:'center' }}>
                  <span style={{color: 'var(--text-main)', fontSize: '0.8rem', fontWeight: 600, padding: '10px'}}>{rec.title}</span>
                </div>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <h3 style={{ fontSize: '1.4rem', margin: '0 0 4px 0', color: 'var(--text-bright)' }}>{rec.title} <span style={{ color: 'var(--text-main)', fontSize: '1rem', fontWeight: 'normal' }}>({rec.release_year})</span></h3>
                      <div style={{ display: 'flex', gap: '6px', marginBottom: '12px', flexWrap: 'wrap' }}>
                        {rec.genres.split('|').map(g => (
                          <span key={g} className="badge badge-blue" style={{ whiteSpace: 'nowrap' }}>{g}</span>
                        ))}
                      </div>
                    </div>
                    
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', background: 'rgba(0, 224, 84, 0.05)', border: '1px solid rgba(0, 224, 84, 0.2)', padding: '10px 16px', borderRadius: '8px' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-main)', textTransform: 'uppercase', letterSpacing: '1px' }}>Match</span>
                      <span style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--accent-green)' }}>{rec.confidence}%</span>
                    </div>
                  </div>

                  <p style={{ color: 'var(--text-main)', fontSize: '0.95rem', lineHeight: '1.5', margin: '4px 0 16px 0', flex: 1 }}>
                    {rec.explanation}
                  </p>

                  <div style={{ display: 'flex', gap: '12px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-main)', alignSelf: 'center', marginRight: 'auto' }}>Critique this:</span>
                    {getDynamicCritiques(rec).map(c => {
                      const Icon = c.icon;
                      return (
                        <button key={c.id} onClick={() => handleCritique(c.type, c.value)} className="secondary-btn" style={{ padding: '6px 12px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Icon size={14} /> {c.label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Right Sidebar: Algorithm Visualisation */}
      <div style={{ width: '320px', flexShrink: 0 }}>
        <div className="glass-panel" style={{ padding: '20px', position: 'sticky', top: '100px', height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1.1rem', marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
            <Activity size={18} color="var(--accent-orange)" /> Algorithm State
          </h3>
          
          <div style={{ marginBottom: '16px', fontSize: '0.9rem', color: 'var(--text-bright)' }}>
            <strong>Status:</strong> {algoMessage || "Idle"}
          </div>

          <div style={{ 
            flex: 1, 
            overflowY: 'auto', 
            background: '#101418', 
            borderRadius: '6px', 
            padding: '12px',
            fontFamily: 'monospace',
            fontSize: '0.8rem',
            border: '1px solid var(--border-color)'
          }}>
            <div style={{ color: 'var(--accent-blue)', marginBottom: '8px' }}>&gt; Initializing Bayesian Update...</div>
            <div style={{ color: 'var(--accent-green)', marginBottom: '12px' }}>[OK] Priors loaded.</div>
            
            {(algoLog && algoLog.length > 0) ? (
              algoLog.map((logStr, i) => (
                <div key={i} style={{ marginBottom: '8px', color: logStr.includes('!!') ? 'var(--accent-orange)' : '#ccc' }}>
                  $ {logStr}
                </div>
              ))
            ) : (
             <div style={{ color: '#888' }}>
               Awaiting CSP execution logs...
             </div> 
            )}
            
            <div style={{ marginTop: '12px', color: 'var(--text-main)', borderTop: '1px dashed #333', paddingTop: '8px' }}>
              &gt; CSP Variable Assignments:
              <br/>- genre: {constraints.genre || 'UNBOUND'}
              <br/>- language: {constraints.language || 'UNBOUND'}
              <br/>- k: {constraints.k}
            </div>
            {constraints.runtime && (
              <div style={{ color: 'var(--accent-orange)', marginTop: '4px' }}>
                &gt; Backtracking: Relaxing... Re-assign runtime {constraints.runtime.join(' ')}
              </div>
            )}
            
            {/* React Force Graph Render */}
            {networkData && networkData.nodes && networkData.nodes.length > 0 && (
              <div style={{ marginTop: '16px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
                <h4 style={{ margin: '0 0 12px 0', fontSize: '0.9rem', color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Activity size={14} /> Network Visualisation
                </h4>
                <div style={{ border: '1px solid var(--border-color)', borderRadius: '6px', overflow: 'hidden', background: '#0a0c0f' }}>
                  <ForceGraph2D
                    graphData={networkData}
                    width={278}
                    height={220}
                    nodeLabel="name"
                    nodeAutoColorBy="group"
                    linkDirectionalArrowLength={3.5}
                    linkDirectionalArrowRelPos={1}
                    linkColor={() => 'rgba(255,255,255,0.2)'}
                    backgroundColor="#0a0c0f"
                    d3AlphaDecay={0.02}
                    d3VelocityDecay={0.3}
                  />
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-main)', marginTop: '8px', textAlign: 'center' }}>
                  Top node dependencies for #1 Match
                </div>
              </div>
            )}
            
          </div>
        </div>
      </div>

    </div>
  );
}
