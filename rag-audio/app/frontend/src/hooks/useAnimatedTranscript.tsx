import { useState, useRef, useEffect } from "react";

/**
 * Animates transcript segments by letter, handling both new and extended segments.
 * @param transcript Array of transcript segments.
 * @returns The animated transcript string.
 */
export default function useAnimatedTranscript(transcript: string[]) {
    const [animatedTranscript, setAnimatedTranscript] = useState<string>("");
    const animationRef = useRef<number | null>(null);
    const lastAnimatedIndex = useRef<number>(-1);

    useEffect(() => {
        if (transcript.length === 0) {
            setAnimatedTranscript("");
            lastAnimatedIndex.current = -1;
            return;
        }

        // If a new segment was added, animate it from the start
        if (transcript.length - 1 > lastAnimatedIndex.current) {
            const segmentToAnimate = transcript[transcript.length - 1];
            let i = 0;
            function animate() {
                setAnimatedTranscript(transcript.slice(0, -1).join("\n") + (transcript.length > 1 ? "\n" : "") + segmentToAnimate.slice(0, i));
                i++;
                if (i <= segmentToAnimate.length) {
                    animationRef.current = window.setTimeout(animate, 18);
                } else {
                    lastAnimatedIndex.current = transcript.length - 1;
                }
            }
            animate();
        } else {
            // If last segment is being extended, animate only the new part
            const lastSegment = transcript[transcript.length - 1];
            const prevSegments = transcript.slice(0, -1).join("\n");
            const prevAnimated = animatedTranscript.slice(prevSegments.length + (transcript.length > 1 ? 1 : 0));
            let i = 0;
            while (i < lastSegment.length && i < prevAnimated.length && lastSegment[i] === prevAnimated[i]) {
                i++;
            }
            function animate(j: number) {
                setAnimatedTranscript(prevSegments + (transcript.length > 1 ? "\n" : "") + lastSegment.slice(0, j));
                if (j < lastSegment.length) {
                    animationRef.current = window.setTimeout(() => animate(j + 1), 18);
                }
            }
            if (i < lastSegment.length) {
                animate(i + 1);
            } else {
                setAnimatedTranscript(transcript.join("\n"));
            }
        }

        return () => {
            if (animationRef.current) clearTimeout(animationRef.current);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [transcript]);

    return animatedTranscript;
}
