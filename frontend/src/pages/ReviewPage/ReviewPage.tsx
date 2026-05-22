import { useState, useRef, useCallback } from 'react';
import type { ReviewFormState, ReviewValidationErrors, RequestState } from '../../types/forms';
import type { ReviewResponse, ReviewRequest } from '../../types/api';
import { validateUserId, validateItemTitle } from '../../utils/validation';
import { buildReviewRequest } from '../../utils/requestBuilder';
import { generateReview } from '../../api/apiClient';
import { ReviewForm } from './ReviewForm';
import { ReviewResult } from './ReviewResult';
import { LoadingSpinner } from '../../components/LoadingSpinner/LoadingSpinner';
import { ErrorBanner } from '../../components/ErrorBanner/ErrorBanner';
import styles from './ReviewPage.module.css';

interface ReviewPageProps {
  formValues: ReviewFormState;
  onFormChange: (values: ReviewFormState) => void;
}

export function ReviewPage({ formValues, onFormChange }: ReviewPageProps) {
  const [requestState, setRequestState] = useState<RequestState<ReviewResponse>>({
    status: 'idle',
    data: null,
    error: null,
  });
  const [lastRequest, setLastRequest] = useState<ReviewRequest | null>(null);
  const [errors, setErrors] = useState<ReviewValidationErrors>({});

  const resultRef = useRef<HTMLDivElement>(null);
  const submitRef = useRef<HTMLButtonElement>(null);

  const validate = (values: ReviewFormState): ReviewValidationErrors => {
    const errs: ReviewValidationErrors = {};
    const userIdErr = validateUserId(values.user_id);
    if (userIdErr) errs.user_id = userIdErr;
    const titleErr = validateItemTitle(values.item_title);
    if (titleErr) errs.item_title = titleErr;
    return errs;
  };

  const executeRequest = useCallback(async (request: ReviewRequest) => {
    // Clear previous results and show loading immediately (Req 6.1, 2.9)
    setRequestState({ status: 'loading', data: null, error: null });
    setLastRequest(request);

    const result = await generateReview(request);

    if (result.ok) {
      setRequestState({ status: 'success', data: result.data, error: null });
      // Move focus to first result element (Req 5.2)
      requestAnimationFrame(() => resultRef.current?.focus());
    } else {
      setRequestState({ status: 'idle', data: null, error: result.error });
      // Move focus back to submit button on error (Req 5.2)
      requestAnimationFrame(() => submitRef.current?.focus());
    }
  }, []);

  const handleSubmit = useCallback(async () => {
    const validationErrors = validate(formValues);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setErrors({});
    const request = buildReviewRequest(formValues);
    await executeRequest(request);
  }, [formValues, executeRequest]);

  const handleRetry = useCallback(() => {
    if (lastRequest) {
      void executeRequest(lastRequest);
    }
  }, [lastRequest, executeRequest]);

  const isLoading = requestState.status === 'loading';

  return (
    <div className={styles.page}>
      <h2 className={styles.pageTitle}>✍️ Book Review Simulator</h2>
      <p className={styles.pageSubtitle}>
        Enter a user ID and book details to generate an authentic Nigerian-English review
        with a predicted star rating.
      </p>

      <ReviewForm
        values={formValues}
        onChange={onFormChange}
        onSubmit={handleSubmit}
        isLoading={isLoading}
        errors={errors}
        submitRef={submitRef}
      />

      {isLoading && <LoadingSpinner label="Generating your Naija review…" />}

      {requestState.error && (
        <ErrorBanner
          message={requestState.error.message}
          onRetry={handleRetry}
          liveRegionId="review-live-region"
        />
      )}

      {requestState.status === 'success' && requestState.data && (
        <ReviewResult ref={resultRef} result={requestState.data} />
      )}
    </div>
  );
}
