import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const clock = new THREE.Clock();

// Tune these if you want the ant smaller / larger.
const TARGET_MODEL_SIZE = 1.0;   // max dimension after normalization
const FRAME_FIT_OFFSET = 150;    // >1 pushes camera farther back

function initHeroViewer() {
    const container = document.getElementById("ant3d-hero");
    if (!container) return;

    // Basic WebGL capability check.
    if (!("WebGLRenderingContext" in window)) {
        console.warn("WebGL is not supported in this browser; hero viewer disabled.");
        return;
    }

    const rect = container.getBoundingClientRect();
    let width = rect.width || container.clientWidth || 640;
    let height = rect.height || container.clientHeight || 360;

    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(40, width / height, 0.01, 1000);
    camera.position.set(0, 0.5, 4);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    renderer.setSize(width, height);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    renderer.shadowMap.enabled = false;
    renderer.setClearColor(0x000000, 0); // transparent

    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.enablePan = false;
    controls.minDistance = 0.5;
    controls.maxDistance = 20;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.8;

    // Studio-ish lighting.
    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x202020, 0.9);
    hemiLight.position.set(0, 1, 0);
    scene.add(hemiLight);

    const keyLight = new THREE.DirectionalLight(0xffffff, 1.25);
    keyLight.position.set(3, 5, 4);
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0xffffff, 0.5);
    fillLight.position.set(-4, 1, -2);
    scene.add(fillLight);

    const modelGroup = new THREE.Group();
    scene.add(modelGroup);

    let mixer = null;

    const loader = new GLTFLoader();
    const modelUrl = container.getAttribute("data-model-url");
    console.log("Hero viewer: loading model from", modelUrl);

    function frameModel(object) {
        const box = new THREE.Box3().setFromObject(object);
        const size = box.getSize(new THREE.Vector3());
        const center = box.getCenter(new THREE.Vector3());

        const maxSize = Math.max(size.x, size.y, size.z);
        if (!isFinite(maxSize) || maxSize === 0) return;

        // Center and put on “ground”.
        object.position.sub(center);
        object.position.y -= box.min.y;

        const fov = THREE.MathUtils.degToRad(camera.fov);
        const fitHeightDistance = maxSize / (2 * Math.tan(fov / 2));
        const fitWidthDistance = fitHeightDistance / camera.aspect;
        const distance = FRAME_FIT_OFFSET * Math.max(fitHeightDistance, fitWidthDistance);

        const direction = new THREE.Vector3(0.45, 0.35, 1).normalize();
        camera.position.copy(direction.multiplyScalar(distance));
        camera.near = distance / 100;
        camera.far = distance * 100;
        camera.updateProjectionMatrix();

        controls.target.set(0, 0.15, 0);
        controls.maxDistance = distance * 4;
        controls.minDistance = distance / 6;
        controls.update();
    }

    loader.load(
        modelUrl,
        (gltf) => {
            const root = gltf.scene || (gltf.scenes && gltf.scenes[0]);
            if (!root) {
                console.error("Hero viewer: GLB loaded without a scene");
                return;
            }

            root.traverse((node) => {
                if (node.isMesh && node.material && node.material.isMeshStandardMaterial) {
                    node.material.metalness = 0.15;
                    node.material.roughness = 0.35;
                }
            });

            // Normalize model size first.
            const rawBox = new THREE.Box3().setFromObject(root);
            const rawSize = rawBox.getSize(new THREE.Vector3());
            const rawMax = Math.max(rawSize.x, rawSize.y, rawSize.z);
            if (isFinite(rawMax) && rawMax > 0) {
                const scale = TARGET_MODEL_SIZE / rawMax;
                root.scale.setScalar(scale);
            }

            // Auto-play first animation clip, if available.
            if (gltf.animations && gltf.animations.length > 0) {
                mixer = new THREE.AnimationMixer(root);
                const clip = gltf.animations[0];
                const action = mixer.clipAction(clip);
                action.play();
                console.log(
                    "Hero viewer: playing animation clip:",
                    clip.name || "(unnamed)"
                );
            } else {
                console.log("Hero viewer: no animations found in GLB.");
            }

            modelGroup.add(root);
            frameModel(modelGroup);
        },
        undefined,
        (error) => {
            console.error("Hero viewer: failed to load GLB:", error);
        }
    );

    window.addEventListener("resize", () => {
        const r = container.getBoundingClientRect();
        width = r.width || container.clientWidth || width;
        height = r.height || container.clientHeight || height;
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
    });

    function animate() {
        requestAnimationFrame(animate);

        const delta = clock.getDelta();
        if (mixer) {
            mixer.update(delta);
        }
        controls.update(delta);

        renderer.render(scene, camera);
    }

    animate();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initHeroViewer);
} else {
    initHeroViewer();
}
