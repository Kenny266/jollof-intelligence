import { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Header } from './components/Header/Header';
import { ReviewPage } from './pages/ReviewPage/ReviewPage';
import { RecommendPage } from './pages/RecommendPage/RecommendPage';
import { DEFAULT_REVIEW_FORM, DEFAULT_RECOMMEND_FORM } from './types/forms';
import type { ReviewFormState, RecommendFormState } from './types/forms';
import styles from './App.module.css';
import './styles/global.css';

function App() {
  // Form values lifted to App so they survive route changes (Req 6.4)
  const [reviewFormValues, setReviewFormValues] = useState<ReviewFormState>(DEFAULT_REVIEW_FORM);
  const [recommendFormValues, setRecommendFormValues] = useState<RecommendFormState>(DEFAULT_RECOMMEND_FORM);

  return (
    <div className={styles.app}>
      {/* ARIA live regions — mounted at root, always in DOM (Req 5.3) */}
      <div
        id="review-live-region"
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
      />
      <div
        id="recommend-live-region"
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
      />

      <Header />

      <main className={styles.main} id="main-content">
        <Routes>
          <Route
            path="/review"
            element={
              <ReviewPage
                formValues={reviewFormValues}
                onFormChange={setReviewFormValues}
              />
            }
          />
          <Route
            path="/recommend"
            element={
              <RecommendPage
                formValues={recommendFormValues}
                onFormChange={setRecommendFormValues}
              />
            }
          />
          <Route path="*" element={<Navigate to="/review" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
