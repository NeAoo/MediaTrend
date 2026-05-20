export function PromptEditor({
  label,
  value,
  onChange,
  minRows = 8,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  minRows?: number;
}) {
  return (
    <label className="field-block">
      <span>{label}</span>
      <textarea
        className="prompt-textarea"
        rows={minRows}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}
