import type { ConversationTurn } from '../../types/api';
import styles from './ConversationHistory.module.css';

interface ConversationHistoryProps {
  turns: ConversationTurn[];
  onClear: () => void;
}

export function ConversationHistory({ turns, onClear }: ConversationHistoryProps) {
  if (turns.length === 0) return null;

  return (
    <div className={styles.container} aria-label="Conversation history">
      <div className={styles.header}>
        <h3 className={styles.title}>💬 Conversation History</h3>
        <button
          type="button"
          className={styles.clearButton}
          onClick={onClear}
          aria-label="Clear conversation history"
        >
          🗑 Clear conversation
        </button>
      </div>

      <div className={styles.turns} role="log" aria-label="Conversation turns" aria-live="polite">
        {turns.map((turn, index) => (
          <div
            key={index}
            className={`${styles.turn} ${
              turn.role === 'user' ? styles.turnUser : styles.turnAssistant
            }`}
            data-testid="conversation-turn"
          >
            <p className={`${styles.role} ${
              turn.role === 'user' ? styles.roleUser : styles.roleAssistant
            }`}>
              {turn.role === 'user' ? '👤 You' : '🤖 Assistant'}
            </p>
            <p className={styles.content}>{turn.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
