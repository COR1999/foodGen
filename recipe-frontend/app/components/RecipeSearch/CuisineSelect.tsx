import Select from '../ui/Select';

interface CuisineSelectProps {
  value: string;
  onChange: (value: string) => void;
}

const CUISINES = [
  { value: '', label: 'Any Cuisine' },
  { value: 'italian', label: 'Italian' },
  { value: 'chinese', label: 'Chinese' },
  { value: 'mexican', label: 'Mexican' },
  { value: 'indian', label: 'Indian' },
  { value: 'japanese', label: 'Japanese' },
  { value: 'thai', label: 'Thai' },
  { value: 'french', label: 'French' },
  { value: 'mediterranean', label: 'Mediterranean' },
  { value: 'american', label: 'American' },
  { value: 'korean', label: 'Korean' },
  { value: 'greek', label: 'Greek' },
  { value: 'spanish', label: 'Spanish' },
];

export default function CuisineSelect({ value, onChange }: CuisineSelectProps) {
  return (
    <Select
      label="Cuisine"
      options={CUISINES}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}