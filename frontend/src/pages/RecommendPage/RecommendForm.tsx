import type { RecommendFormState, RecommendValidationErrors } from '../../types/forms';
import { FormField } from '../../components/FormField/FormField';
import styles from './RecommendForm.module.css';

interface RecommendFormProps {
  values: RecommendFormState;
  onChange: (values: RecommendFormState) => void;
  onSubmit: () => void;
  isLoading: boolean;
  errors: RecommendValidationErrors;
  submitRef?: React.Ref<HTMLButtonElement>;
}

export function RecommendForm({
  values,
  onChange,
  onSubmit,
  isLoading,
  errors,
  submitRef,
}: RecommendFormProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <form
      className={styles.form}
      onSubmit={handleSubmit}
      noValidate
      aria-label="Book Recommender form"
    >
      <h2 className={styles.formTitle}>📚 Get Personalised Book Recommendations</h2>

      <FormField
        id="recommend-user-id"
        label="User ID"
        value={values.user_id}
        onChange={(v) => onChange({ ...values, user_id: v })}
        required
        error={errors.user_id}
        placeholder="e.g. AFKZENTNBQ7A7V7UXW5JJI6UGRYQ"
        disabled={isLoading}
      />

      <FormField
        id="recommend-context"
        label="What are you looking for?"
        value={values.context}
        onChange={(v) => onChange({ ...values, context: v })}
        as="textarea"
        rows={4}
        required
        error={errors.context}
        placeholder="e.g. Looking for something similar to Things Fall Apart but set in modern Nigeria…"
        disabled={isLoading}
      />

      <FormField
        id="recommend-top-k"
        label="Number of Recommendations"
        value={String(values.top_k)}
        onChange={(v) => onChange({ ...values, top_k: parseInt(v, 10) || 5 })}
        type="number"
        error={errors.top_k}
        placeholder="5"
        disabled={isLoading}
      />
      <p className={styles.topKHint}>Enter a number between 1 and 20 (default: 5)</p>

      <button
        ref={submitRef}
        type="submit"
        className={styles.submitButton}
        disabled={isLoading}
        aria-label="Get book recommendations"
      >
        {isLoading ? '⏳ Finding books…' : '🔍 Get Recommendations'}
      </button>
    </form>
  );
}
