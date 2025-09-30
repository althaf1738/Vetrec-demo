import { highlightChange } from "../utils/diff";

type Note = { subjective:string; objective:string; assessment:string; plan:string };

export default function DiffPanel({before, after}:{before: Note; after: Note}){
  const fields = [
    ["subjective","Subjective"],
    ["objective","Objective"],
    ["assessment","Assessment"],
    ["plan","Plan"],
  ] as const;

  const items = fields.map(([k,label])=>{
    const {beforeHtml, afterHtml, changed} = highlightChange(
      (before as any)[k] || "",
      (after as any)[k] || ""
    );
    return { key:k, label, beforeHtml, afterHtml, changed };
  });

  const changedItems = items.filter(i => i.changed);

  if (changedItems.length === 0) {
    return (
      <div className="help">
        No edits yet. Change any field in the Editor to see differences here.
      </div>
    );
  }

  return (
    <div className="diff-wrap">
      {changedItems.map(i=>(
        <div key={i.key} className="diff-block">
          <div className="diff-title">{i.label} • changed</div>
          <div className="grid2 mono small">
            <div>
              <div className="help">Before</div>
              <div className="diff-line" dangerouslySetInnerHTML={{__html: i.beforeHtml}} />
            </div>
            <div>
              <div className="help">After</div>
              <div className="diff-line" dangerouslySetInnerHTML={{__html: i.afterHtml}} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
