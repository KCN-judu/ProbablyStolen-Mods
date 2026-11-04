// Wraps every table in a `.table-scroll` box. The box scrolls sideways when a table is wider than the page, and the
// table itself stays a real table that fills the box, so its header row spans the whole frame. (Making the <table>
// element `display: block` to scroll left its inner table as wide as its content only, and the header stopped short
// of the frame.)
import { visit } from 'unist-util-visit';

export default function rehypeTableScroll() {
  return (tree) => {
    visit(tree, 'element', (node, index, parent) => {
      if (node.tagName !== 'table' || !parent || index === undefined) return;
      if (parent.type === 'element' && parent.properties?.className?.includes?.('table-scroll')) return;
      parent.children[index] = {
        type: 'element',
        tagName: 'div',
        properties: { className: ['table-scroll'] },
        children: [node],
      };
      return 'skip';
    });
  };
}
