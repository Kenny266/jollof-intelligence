import type { ReviewFormState, ReviewValidationErrors } from '../../types/forms';
import { FormField } from '../../components/FormField/FormField';
import styles from './ReviewForm.module.css';

interface ReviewFormProps {
  values: ReviewFormState;
  onChange: (values: ReviewFormState) => void;
  onSubmit: () => void;
  isLoading: boolean;
  errors: ReviewValidationErrors;
  submitRef?: React.Ref<HTMLButtonElement>;
}

export function ReviewForm({
  values,
  onChange,
  onSubmit,
  isLoading,
  errors,
  submitRef,
}: ReviewFormProps) {
  const set = (field: keyof ReviewFormState) => (value: string) =>
    onChange({ ...values, [field]: value });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <form
      className={styles.form}
      onSubmit={handleSubmit}
      noValidate
      aria-label="Book Review Simulator form"
    >
      <h2 className={styles.formTitle}>📖 Generate a Nigerian-English Book Review</h2>

      <FormField
        id="review-user-id"
        label="User ID"
        value={values.user_id}
        onChange={set('user_id')}
        required
        error={errors.user_id}
        placeholder="e.g. AFKZENTNBQ7A7V7UXW5JJI6UGRYQ"
        disabled={isLoading}
      />

      <FormField
        id="review-item-title"
        label="Book Title"
        value={values.item_title}
        onChange={set('item_title')}
        required
        error={errors.item_title}
        placeholder="e.g. Things Fall Apart"
        disabled={isLoading}
      />

      <div className={styles.row}>
        <FormField
          id="review-author"
          label="Author"
          value={values.author}
          onChange={set('author')}
          placeholder="e.g. Chinua Achebe"
          disabled={isLoading}
        />
        <FormField
          id="review-price"
          label="Price"
          value={values.price}
          onChange={set('price')}
          placeholder="e.g. 12.99"
          disabled={isLoading}
        />
      </div>

      <FormField
        id="review-categories"
        label="Categories"
        value={values.categories}
        onChange={set('categories')}
        placeholder="e.g. Books > Literature & Fiction > African Literature"
        disabled={isLoading}
      />

      <FormField
        id="review-description"
        label="Description"
        value={values.description}
        onChange={set('description')}
        as="textarea"
        rows={3}
        placeholder="Brief description of the book…"
        disabled={isLoading}
      />

      <button
        ref={submitRef}
        type="submit"
        className={styles.submitButton}
        disabled={isLoading}
        aria-label="Generate book review"
      >
        {isLoading ? '⏳ Generating…' : '✨ Generate Review'}
      </button>
    </form>
  );
}
