// prose-eval, 28 s product video, v2 (16:9): the user-story arc (lecture/user-journeys) with the reference transfer
// (refs/transfer.md) — orbs for the models, isolated components on flat fields, a 120 BPM grid, black dot end card.
import { Composition, registerRoot } from "raea";
import { Cut2 } from "../components/cut2";
import { score } from "./score";

const Root = () => (<><Cut2 />{score()}</>);
registerRoot(() => <Composition id="prose-v2" component={Root} width={1920} height={1080} fps={30} durationInFrames={840} />);
