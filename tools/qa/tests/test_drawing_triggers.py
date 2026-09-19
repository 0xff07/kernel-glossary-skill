"""kind: rule — a DETAILS subsection whose prose or excerpts carry a shape of the trigger table and no figure is listed."""
import unittest
from checks import drawing_triggers as rule
from tests.support import FIGURE, page, skeleton, observed
PROSE = 'The ring keeps its indexes in one record and nothing else touches them.'
ENUM = '```c\n/* drivers/kg/ring.h:20 */\nenum kg_state {\n\tKG_IDLE,\n\tKG_ARMED,\n\tKG_RUNNING,\n\tKG_DRAINING,\n};\n```'
STRUCT = '```c\n/* drivers/kg/ring.h:30 */\nstruct kg_big {\n\tint a;\n\tint b;\n\tint c;\n\tint d;\n\tint e;\n\tint f;\n};\n```'
RESHAPE = '```c\n/* drivers/kg/ring.c:40 */\n\tring = kzalloc_obj(*ring);\n\tlist_add_tail(&ring->list, &kg->rings);\n```'
TOPO = '```c\n/* drivers/kg/ring.c:50 */\n\tparent = tb_switch_parent(sw);\n```'

def run(details):
    return observed(rule.check(page(skeleton(details=details)), None))

def kinds(found):
    return [sorted(f.data['triggers']) for f in found.all if f.severity == 'review']

class Triggers(unittest.TestCase):
    def test_each_shape_is_recognised(self):
        self.assertEqual(kinds(run(f'### A\n\n{PROSE}\n\n{ENUM}\n\n{PROSE}\n')), [['state-set']])
        self.assertEqual(kinds(run(f'### A\n\n{PROSE}\n\n{STRUCT}\n\n{PROSE}\n')), [['layout']])
        self.assertEqual(kinds(run(f'### A\n\n{PROSE}\n\n{RESHAPE}\n\n{PROSE}\n')), [['reshaping']])
        self.assertEqual(kinds(run(f'### A\n\n{PROSE}\n\n{TOPO}\n\n{PROSE}\n')), [['topology']])
        actors = 'The parent router asks and the child router answers, then the parent writes what the child reported.'
        self.assertEqual(kinds(run(f'### A\n\n{actors}\n')), [['actors']])
        steps = 'First, the producer claims a slot. Then, it fills the slot. Finally, it publishes the head.'
        self.assertEqual(kinds(run(f'### A\n\n{steps}\n')), [['sequence']])

    def test_a_figure_or_no_shape_leaves_the_subsection_alone(self):
        found = run(f'### A\n\n{PROSE}\n\n{ENUM}\n\n{PROSE}\n\n{FIGURE}\n\n{PROSE}\n')
        self.assertEqual(kinds(found), [])
        self.assertEqual(found.footer, 'subsections=1 with-figure=1 candidates=0 state-set=0 actors=0 layout=0 reshaping=0 topology=0 sequence=0')
        found = run(f'### A\n\n{PROSE}\n')
        self.assertEqual(found.footer, 'subsections=1 with-figure=0 candidates=0 state-set=0 actors=0 layout=0 reshaping=0 topology=0 sequence=0')
if __name__ == '__main__':
    unittest.main()
