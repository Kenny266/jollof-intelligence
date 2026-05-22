import type { ChangeEvent } from 'react';
import styles from './FormField.module.css';

interface FormFieldBaseProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  required?: boolean;
  placeholder?: string;
  disabled?: boolean;
}

interface InputFieldProps extends FormFieldBaseProps {
  as?: 'input';
  type?: 'text' | 'number' | 'email';
}

interface TextareaFieldProps extends FormFieldBaseProps {
  as: 'textarea';
  rows?: number;
}

type FormFieldProps = InputFieldProps | TextareaFieldProps;

export function FormField(props: FormFieldProps) {
  const {
    id,
    label,
    value,
    onChange,
    error,
    required = false,
    placeholder,
    disabled = false,
  } = props;

  const errorId = `${id}-error`;
  const hasError = Boolean(error);

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  return (
    <div className={styles.field}>
      <label htmlFor={id} className={styles.label}>
        {label}
        {required && <span className={styles.required} aria-hidden="true"> *</span>}
        {!required && <span className={styles.optional}>(optional)</span>}
      </label>

      {props.as === 'textarea' ? (
        <textarea
          id={id}
          className={`${styles.textarea} ${hasError ? styles.hasError : ''}`}
          value={value}
          onChange={handleChange}
          aria-label={label}
          aria-required={required}
          aria-invalid={hasError}
          aria-describedby={hasError ? errorId : undefined}
          placeholder={placeholder}
          disabled={disabled}
          rows={props.rows ?? 4}
        />
      ) : (
        <input
          id={id}
          type={props.type ?? 'text'}
          className={`${styles.input} ${hasError ? styles.hasError : ''}`}
          value={value}
          onChange={handleChange}
          aria-label={label}
          aria-required={required}
          aria-invalid={hasError}
          aria-describedby={hasError ? errorId : undefined}
          placeholder={placeholder}
          disabled={disabled}
        />
      )}

      {hasError && (
        <span id={errorId} className={styles.error} role="alert">
          {error}
        </span>
      )}
    </div>
  );
}
