
/**
 * Hero viewer for the 3D ant model.
 * Loads guide/models/ant.glb into the #ant3d-hero container.
 * Uses THREE from the CDN and the local GLTFLoader helper.
 */
(function () {
    function initHeroAnt() {
        var container = document.getElementById("ant3d-hero");
        if (!container) {
            return;
        }

        if (typeof THREE === "undefined") {
            console.warn("THREE is not available; hero ant disabled.");
            return;
        }

        // Select a GLTF loader implementation.
        var LoaderCtor = null;
        if (typeof THREE.GLTFLoader === "function") {
            LoaderCtor = THREE.GLTFLoader;
        } else if (typeof GLTFLoader === "function") {
            try {
                LoaderCtor = GLTFLoader(THREE);
            } catch (err) {
                console.error("Legacy GLTFLoader present but failed to initialize:", err);
            }
        }

        if (!LoaderCtor) {
            console.warn("No GLTF loader found (THREE.GLTFLoader or GLTFLoader factory); hero ant disabled.");
            return;
        }

        var rect = container.getBoundingClientRect();
        var width = rect.width || container.clientWidth || 640;
        var height = rect.height || container.clientHeight || 320;

        var scene = new THREE.Scene();

        var camera = new THREE.PerspectiveCamera(35, width / height, 0.1, 100);
        camera.position.set(0.2, 0.5, 2.0);

        var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setPixelRatio(window.devicePixelRatio || 1);
        renderer.setSize(width, height);
        renderer.shadowMap.enabled = false;

        container.innerHTML = "";
        container.appendChild(renderer.domElement);

        // Lighting
        var hemiLight = new THREE.HemisphereLight(0xffffff, 0x202020, 1.1);
        hemiLight.position.set(0, 1, 0);
        scene.add(hemiLight);

        var dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
        dirLight.position.set(3, 4, 2);
        scene.add(dirLight);

        // Ground disk
        var groundGeom = new THREE.CircleGeometry(1.2, 64);
        var groundMat = new THREE.MeshStandardMaterial({
            color: 0x111c12,
            roughness: 0.95,
            metalness: 0.0
        });
        var ground = new THREE.Mesh(groundGeom, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = -0.4;
        scene.add(ground);

        var modelGroup = new THREE.Group();
        scene.add(modelGroup);

        var loader = new LoaderCtor();
        var modelUrl = container.getAttribute("data-model-url");
        if (!modelUrl) {
            console.warn("Hero ant: no data-model-url attribute set; nothing to load.");
        } else {
            console.log("Hero ant: loading model from", modelUrl);
            loader.load(
                modelUrl,
                function (gltf) {
                    var root = gltf.scene || (gltf.scenes && gltf.scenes[0]);
                    if (!root) {
                        console.error("Hero ant: GLB loaded without a scene.");
                        return;
                    }

                    root.traverse(function (node) {
                        if (node.isMesh) {
                            node.castShadow = false;
                            node.receiveShadow = false;
                            if (node.material && node.material.isMeshStandardMaterial) {
                                node.material.metalness = 0.1;
                                node.material.roughness = 0.4;
                            }
                        }
                    });

                    var box = new THREE.Box3().setFromObject(root);
                    var size = new THREE.Vector3();
                    var center = new THREE.Vector3();
                    box.getSize(size);
                    box.getCenter(center);

                    root.position.sub(center);
                    root.position.y -= box.min.y;

                    var maxDim = Math.max(size.x, size.y, size.z);
                    if (maxDim > 0) {
                        var targetSize = 1.2;
                        var scale = targetSize / maxDim;
                        root.scale.setScalar(scale);
                    }

                    modelGroup.add(root);
                },
                undefined,
                function (error) {
                    console.error("Hero ant: failed to load GLB:", error);
                }
            );
        }

        var clock = new THREE.Clock();
        var baseRotation = 0.6;
        var targetRotationOffset = 0;
        var currentRotationOffset = 0;

        container.addEventListener("pointermove", function (event) {
            var bounds = container.getBoundingClientRect();
            var x = (event.clientX - bounds.left) / bounds.width - 0.5;
            targetRotationOffset = x * 0.7;
        });

        container.addEventListener("pointerleave", function () {
            targetRotationOffset = 0;
        });

        window.addEventListener("resize", function () {
            var r = container.getBoundingClientRect();
            var w = r.width || container.clientWidth || width;
            var h = r.height || container.clientHeight || height;
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
        });

        function animate() {
            requestAnimationFrame(animate);

            var delta = clock.getDelta();
            currentRotationOffset += (targetRotationOffset - currentRotationOffset) * 4 * delta;

            modelGroup.rotation.y = baseRotation + currentRotationOffset;
            renderer.render(scene, camera);
        }

        animate();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initHeroAnt);
    } else {
        initHeroAnt();
    }
})();
