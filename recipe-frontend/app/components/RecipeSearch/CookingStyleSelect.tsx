import Select from '../ui/Select';

interface CookingStyleSelectProps {
  value: string;
  onChange: (value: string) => void;
}

const COOKING_STYLES = [
  { value: '', label: 'Any Style' },
  { value: 'baked', label: 'Baked' },
  { value: 'grilled', label: 'Grilled' },
  { value: 'fried', label: 'Fried' },
  { value: 'slow-cooked', label: 'Slow Cooked' },
  { value: 'steamed', label: 'Steamed' },
  { value: 'stir-fried', label: 'Stir Fried' },
  { value: 'roasted', label: 'Roasted' },
  { value: 'no-cook', label: 'No Cook / Raw' },
  { value: 'one-pot', label: 'One Pot' },
];

export default function CookingStyleSelect({ value, onChange }: CookingStyleSelectProps) {
  return (
    <Select
      label="Cooking Style"
      options={COOKING_STYLES}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}