import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { crackHash, type Special } from './api'

type Props = {
  /** Algorithm to crack, e.g. "md5". */
  algorithm: string
  /** Expected hex length for this algorithm (md5 = 32), used for a hint. */
  hexLength: number
}

function CrackerTab({ algorithm, hexLength }: Props) {
  const [hash, setHash] = useState('')
  const [useRules, setUseRules] = useState(true)
  const [seedWords, setSeedWords] = useState('')
  const [bruteForce, setBruteForce] = useState(false)
  const [length, setLength] = useState('')
  const [special, setSpecial] = useState<Special>('unknown')
  const [bruteAround, setBruteAround] = useState(false)

  const mutation = useMutation({
    mutationFn: () =>
      crackHash(hash, {
        algorithm,
        useRules,
        extraWords: seedWords
          .split(/[\s,]+/)
          .map((w) => w.trim())
          .filter(Boolean),
        bruteForce,
        length: length.trim() === '' ? null : Number(length),
        special,
        bruteAround,
      }),
  })

  const trimmed = hash.trim()
  const isHex = /^[0-9a-fA-F]*$/.test(trimmed)
  const validLength = trimmed.length === hexLength
  const canSubmit = trimmed.length > 0 && isHex && validLength && !mutation.isPending

  function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (canSubmit) mutation.mutate()
  }

  const result = mutation.data

  return (
    <div className="cracker">
      <form onSubmit={onSubmit} className="cracker-form">
        <label htmlFor="hash-input" className="cracker-label">
          {algorithm.toUpperCase()} hash (hex string)
        </label>
        <input
          id="hash-input"
          className="cracker-input"
          type="text"
          autoComplete="off"
          spellCheck={false}
          placeholder={`Paste a ${hexLength}-character ${algorithm.toUpperCase()} hash…`}
          value={hash}
          onChange={(e) => setHash(e.target.value)}
        />

        {trimmed.length > 0 && !isHex && (
          <p className="cracker-warn">Only hex characters (0–9, a–f) are allowed.</p>
        )}
        {trimmed.length > 0 && isHex && !validLength && (
          <p className="cracker-warn">
            {algorithm.toUpperCase()} hashes are {hexLength} characters — you have{' '}
            {trimmed.length}.
          </p>
        )}

        <label htmlFor="seed-input" className="cracker-label">
          Hint words (optional)
        </label>
        <input
          id="seed-input"
          className="cracker-input"
          type="text"
          autoComplete="off"
          spellCheck={false}
          placeholder="e.g. your name — mors, anup …"
          value={seedWords}
          onChange={(e) => setSeedWords(e.target.value)}
        />

        <label className="cracker-toggle">
          <input
            type="checkbox"
            checked={useRules}
            onChange={(e) => setUseRules(e.target.checked)}
          />
          <span>
            Apply rules — mutate words (Mors → <code>Mors123</code>, <code>M0rs!</code>)
          </span>
        </label>

        <label className="cracker-toggle">
          <input
            type="checkbox"
            checked={bruteForce}
            onChange={(e) => setBruteForce(e.target.checked)}
          />
          <span>
            Smart brute-force — try hint word + numbers (<code>anup</code> →{' '}
            <code>anup77353</code>)
          </span>
        </label>

        {bruteForce && (
          <div className="brute-options">
            <p className="brute-hint">
              Answer what you know — it shrinks the search and saves compute.
            </p>
            <div className="brute-row">
              <label className="brute-field">
                <span>Password length</span>
                <input
                  type="number"
                  min={1}
                  max={64}
                  placeholder="e.g. 9"
                  value={length}
                  onChange={(e) => setLength(e.target.value)}
                />
              </label>
              <label className="brute-field">
                <span>Special characters?</span>
                <select
                  value={special}
                  onChange={(e) => setSpecial(e.target.value as Special)}
                >
                  <option value="unknown">Not sure</option>
                  <option value="no">No (none)</option>
                  <option value="yes">Yes (has one)</option>
                </select>
              </label>
            </div>

            <label className="cracker-toggle">
              <input
                type="checkbox"
                checked={bruteAround}
                onChange={(e) => setBruteAround(e.target.checked)}
              />
              <span>
                Numbers can be before/around the word (<code>45akash5465</code>)
              </span>
            </label>
          </div>
        )}

        <button type="submit" className="cracker-button" disabled={!canSubmit}>
          {mutation.isPending ? 'Cracking…' : 'Crack it'}
        </button>
      </form>

      {mutation.isError && (
        <div className="cracker-result error">
          {(mutation.error as Error).message}
        </div>
      )}

      {result && !mutation.isPending && (
        <div className={`cracker-result ${result.found ? 'found' : 'notfound'}`}>
          {result.found ? (
            <>
              <span className="result-label">Password found</span>
              <code className="result-password">{result.password}</code>
              <p className="result-meta">
                {result.attempts.toLocaleString()} attempts ·{' '}
                {result.duration_ms.toFixed(1)} ms · wordlist:{' '}
                {result.wordlist ?? 'n/a'}
              </p>
            </>
          ) : (
            <>
              <span className="result-label">Not found</span>
              <p className="result-meta">
                This hash isn't in the wordlist
                {result.wordlist ? ` (${result.wordlist})` : ''}. Tried{' '}
                {result.attempts.toLocaleString()} candidates.
              </p>
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default CrackerTab
