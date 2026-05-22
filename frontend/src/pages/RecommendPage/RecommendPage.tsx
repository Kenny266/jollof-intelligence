import { useState, useRef, useCallback } from 'react';
import type { RecommendFormState, RecommendValidationErrors, RequestState } from '../../types/forms';
import type { RecommendResponse, RecommendRequest, ConversationTurn } from '../../types/api';
import { validateUserId, validateContext, validateTopK } from '../../utils/validation';
import { buildRecommendRequest } from '../../utils/requestBuilder';
import { getRecommendations } from '../../api/apiClient';
import { RecommendForm } from './RecommendForm';
import { RecommendationCard } from './RecommendationCard';
import { FollowUpBanner } from './FollowUpBanner';
import { ConversationHistory } from '../../components/ConversationHistory/ConversationHistory';
import { ColdStartBadge } from '../../components/ColdStartBadge/ColdStartBadge';
import { LoadingSpinner } from '../../components/LoadingSpinner/LoadingSpinner';
import { ErrorBanner } from '../../components/ErrorBanner/ErrorBanner';
import styles from './RecommendPage.module.css';

interface RecommendPageProps {
  formValues: RecommendFormState;
  onFormChange: (values: RecommendFormState) => void;
}

export function RecommendPage({ formValues, onFormChange }: RecommendPageProps) {
  const [requestState, setRequestState] = useState<RequestState<RecommendResponse>>({
    status: 'idle',
    data: null,
    error: null,
  });
  const [lastRequest, setLastRequest] = useState<RecommendRequest | null>(null);
  const [conversation, setConversation] = useState<ConversationTurn[]>([]);
  const [errors, setErrors] = useState<RecommendValidationErrors>({});

  const firstCardRef = useRef<HTMLDivElement>(null);
  const submitRef = useRef<HTMLButtonElement>(null);

  const validate = (values: RecommendFormState): RecommendValidationErrors => {
    const errs: RecommendValidationErrors = {};
    const userIdErr = validateUserId(values.user_id);
    if (userIdErr) errs.user_id = userIdErr;
    const contextErr = validateContext(values.context);
    if (contextErr) errs.context = contextErr;
    const topKErr = validateTopK(values.top_k);
    if (topKErr) errs.top_k = topKErr;
    return errs;
  };

  const executeRequest = useCallback(async (request: RecommendRequest) => {
    setRequestState({ status: 'loading', data: null, error: null });
    setLastRequest(request);

    const result = await getRecommendations(request);

    if (result.ok) {
      const response = result.data;
      // Append user + assistant turns to conversation history (Req 3.7, 3.8)
      setConversation((prev) => [
        ...prev,
        { role: 'user', content: request.context },
        {
          role: 'assistant',
          content:
            response.recommendations.length > 0
              ? `I recommended: ${response.recommendations.map((r) => r.title).join(', ')}.`
              : 'No recommendations found for this context.',
        },
      ]);
      setRequestState({ status: 'success', data: response, error: null });
      // Move focus to first recommendation card (Req 5.2)
      requestAnimationFrame(() => firstCardRef.current?.focus());
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
    const request = buildRecommendRequest(formValues, conversation);
    await executeRequest(request);
  }, [formValues, conversation, executeRequest]);

  const handleRetry = useCallback(() => {
    if (lastRequest) {
      void executeRequest(lastRequest);
    }
  }, [lastRequest, executeRequest]);

  const handleClearConversation = useCallback(() => {
    setConversation([]);
    setRequestState({ status: 'idle', data: null, error: null });
    setLastRequest(null);
  }, []);

  const isLoading = requestState.status === 'loading';
  const recommendations = requestState.data?.recommendations ?? [];

  return (
    <div className={styles.page}>
      <h2 className={styles.pageTitle}>📚 Personalised Book Recommender</h2>
      <p className={styles.pageSubtitle}>
        Tell us what you're looking for and we'll find the perfect books for you —
        with authentic Naija reasons why you'll love them.
      </p>

      <ConversationHistory turns={conversation} onClear={handleClearConversation} />

      <RecommendForm
        values={formValues}
        onChange={onFormChange}
        onSubmit={handleSubmit}
        isLoading={isLoading}
        errors={errors}
        submitRef={submitRef}
      />

      {isLoading && <LoadingSpinner label="Finding your perfect books…" />}

      {requestState.error && (
        <ErrorBanner
          message={requestState.error.message}
          onRetry={handleRetry}
          liveRegionId="recommend-live-region"
        />
      )}

      {requestState.status === 'success' && (
        <>
          {requestState.data?.cold_start && <ColdStartBadge feature="recommend" />}

          {recommendations.length === 0 ? (
            <div className={styles.emptyState} role="status">
              😕 No recommendations found — try a different context or user ID.
            </div>
          ) : (
            <>
              <p className={styles.resultsHeader}>
                🎯 Found {recommendations.length} recommendation{recommendations.length !== 1 ? 's' : ''} for you:
              </p>
              <div className={styles.resultsList}>
                {recommendations.map((rec, index) => (
                  <RecommendationCard
                    key={rec.item_id || index}
                    recommendation={rec}
                    ref={index === 0 ? firstCardRef : undefined}
                  />
                ))}
              </div>
            </>
          )}

          {requestState.data?.follow_up && (
            <FollowUpBanner followUp={requestState.data.follow_up} />
          )}
        </>
      )}
    </div>
  );
}
