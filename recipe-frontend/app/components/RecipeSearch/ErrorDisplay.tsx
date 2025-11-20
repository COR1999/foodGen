interface ErrorDisplayProps {
  message: string;
  onDismiss?: () => void;
}

export default function ErrorDisplay({ message, onDismiss }: ErrorDisplayProps) {
  return (
    <div className="bg-red-50 border-2 border-red-200 text-red-700 px-4 py-4 rounded-lg mb-4 flex items-start justify-between">
      <div>
        <p className="font-bold">Something went wrong</p>
        <p className="text-sm mt-1">{message}</p>
      </div>
      {onDismiss && (
        <button 
          onClick={onDismiss}
          className="text-red-500 hover:text-red-700 font-bold text-xl leading-none"
        >
          ×
        </button>
      )}
    </div>
  );
}
