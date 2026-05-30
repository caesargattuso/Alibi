import { useState, useEffect, useCallback } from "react";
import { sceneService, type Scene, type MapData, type Interactable, type InteractResult } from "../services/scenes";

export function useScene(sceneId: number | null) {
  const [scene, setScene] = useState<Scene | null>(null);
  const [mapData, setMapData] = useState<MapData | null>(null);
  const [interactables, setInteractables] = useState<Interactable[]>([]);

  const loadScene = useCallback(async (id: number) => {
    const [sceneRes, mapRes, interactRes] = await Promise.all([
      sceneService.get(id),
      sceneService.getMap(id),
      sceneService.getInteractables(id),
    ]);
    setScene(sceneRes.data.data);
    setMapData(mapRes.data.data);
    setInteractables(interactRes.data.data.interactables);
  }, []);

  useEffect(() => {
    if (sceneId) loadScene(sceneId);
  }, [sceneId, loadScene]);

  const executeInteraction = useCallback(
    async (sessionId: number, interactableId: string, actionId: string): Promise<InteractResult | null> => {
      if (!sceneId) return null;
      const { data } = await sceneService.interact(sceneId, {
        session_id: sessionId,
        interactable_id: interactableId,
        action_id: actionId,
      });
      return data.data;
    },
    [sceneId]
  );

  return { scene, mapData, interactables, loadScene, executeInteraction };
}
