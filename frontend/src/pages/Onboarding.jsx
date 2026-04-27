import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function Onboarding() {
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState(1);
  const [maxUserId, setMaxUserId] = useState(1);
  const [ratings, setRatings] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch initial domains for max_user_id
    axios.get('http://127.0.0.1:8000/movies/domains')
      .then(res => {
        if (res.data.max_user_id) setMaxUserId(res.data.max_user_id);
      })
      .catch(err => console.error(err));

    axios.get('http://127.0.0.1:8000/movies?limit=12')
      .then(res => {
        setMovies(res.data.movies);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching movies", err);
        setLoading(false);
      });
  }, []);

  const handleRate = (id, rating) => {
    setRatings(prev => ({ ...prev, [id]: rating }));
  };

  const handleProceed = () => {
    // Navigate with state containing user Id
    navigate('/recommendations', { state: { userId } });
  };

  return (
    <div className="container animate-fade-in" style={{ padding: '40px 24px' }}>
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '12px', letterSpacing: '-1px' }}>Welcome to CineMatch.</h1>
        <p style={{ fontSize: '1.2rem', color: 'var(--text-main)', maxWidth: '600px', margin: '0 auto' }}>
          Rate a few movies you've seen, and our hybrid Bayesian-CSP engine will find what you should watch next.
        </p>
      </div>

      <div style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        gap: '8px',
        marginBottom: '60px',
        padding: '20px',
        background: 'var(--glass-bg)',
        borderRadius: '12px',
        border: '1px solid var(--glass-border)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span>Join as User ID:</span>
          <input
            type="number"
            min="1"
            max={maxUserId}
            value={userId}
            onChange={e => {
              const val = Math.max(1, Math.min(maxUserId, Number(e.target.value)));
              setUserId(val);
            }}
            className="input-field"
            style={{ width: '80px' }}
          />
          <button onClick={handleProceed} className="primary-btn">
            View Recommendations
          </button>
        </div>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-main)', marginTop: '4px' }}>
          Users in the database: {maxUserId}
        </div>
      </div>

      <h2 style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '30px' }}>Popular Films</h2>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>Loading films...</div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
          gap: '24px'
        }}>
          {movies.map((movie, idx) => (
            <div key={movie.movieId} className="glass-panel delay-1 animate-fade-in" style={{ padding: '16px', display: 'flex', flexDirection: 'column' }}>
              <div style={{
                height: '280px',
                background: 'linear-gradient(to bottom, #2c3440, #14181c)',
                borderRadius: '8px',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-main)',
                fontSize: '0.9rem',
                border: '1px solid var(--border-color)',
                textAlign: 'center',
                padding: '10px'
              }}>
                <span style={{ fontWeight: 'bold', color: 'var(--text-bright)' }}>{movie.title}</span>
              </div>
              <div style={{ flex: 1 }}>
                <h3 style={{ fontSize: '1rem', margin: '0 0 8px 0', lineHeight: '1.4' }}>{movie.title}</h3>
                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                  {String(movie.genres).split('|').slice(0, 2).map(g => (
                    <span key={g} className="badge badge-blue">{g}</span>
                  ))}
                </div>
              </div>

              <div style={{ marginTop: '16px', borderTop: '1px solid var(--border-color)', paddingTop: '12px', display: 'flex', justifyContent: 'space-between' }}>
                {[1, 2, 3, 4, 5].map(star => (
                  <button
                    key={star}
                    onClick={() => handleRate(movie.movieId, star)}
                    style={{
                      background: 'none',
                      color: ratings[movie.movieId] >= star ? 'var(--accent-green)' : 'var(--text-main)',
                      fontSize: '1.2rem',
                      opacity: ratings[movie.movieId] >= star ? 1 : 0.5
                    }}
                  >
                    ★
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
