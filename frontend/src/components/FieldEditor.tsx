interface Props {
  fields: Record<string, string | string[] | null>;
  editedFields: Record<string, string>;
  onChange: (key: string, value: string) => void;
}

const FIELD_LABELS: Record<string, string> = {
  company_name: 'Company Name',
  registration_number: 'Registration Number',
  date_of_filing: 'Date of Filing',
  effective_date: 'Effective Date',
  registered_agent: 'Registered Agent',
  signatories: 'Signatories',
  jurisdiction: 'Jurisdiction',
};

export default function FieldEditor({ fields, editedFields, onChange }: Props) {
  return (
    <div className="space-y-3">
      {Object.entries(fields).map(([key, originalValue]) => {
        const display = Array.isArray(originalValue)
          ? originalValue.join(', ')
          : originalValue ?? '';
        const edited = editedFields[key];
        const isEdited = edited !== undefined && edited !== display;

        return (
          <div key={key}>
            <label className="block text-xs text-slate-500 mb-1">
              {FIELD_LABELS[key] || key.replace(/_/g, ' ')}
            </label>
            <input
              type="text"
              value={edited ?? display}
              onChange={(e) => onChange(key, e.target.value)}
              className={`w-full px-3 py-1.5 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                isEdited
                  ? 'border-amber-400 bg-amber-50'
                  : 'border-slate-300 bg-white'
              }`}
            />
            {isEdited && (
              <p className="text-xs text-amber-600 mt-0.5">
                Original: {display || '(empty)'}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
