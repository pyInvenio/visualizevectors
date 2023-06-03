<script lang="ts" type="module">
	import { UMAP } from 'umap-js';
	import * as THREE from 'three';
	import { onMount } from 'svelte';
	import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
	import { parse } from 'postcss';
	let canvas: HTMLCanvasElement;
	const umap = new UMAP({
		nComponents: 3,
		nEpochs: 100,
		nNeighbors: 10
	});
	let thread_id_num = 0;
	let chat_data = '';

	const coorddata: any[] = [];
	let data = {};
	let result: number[][] = [];
	let outlinedObjects = [];

	const renderPoints = (data: any) => {
		const raycaster = new THREE.Raycaster();
		const mouse = new THREE.Vector2();

		const scene = new THREE.Scene();
		const camera = new THREE.PerspectiveCamera(
			75,
			window.innerWidth / window.innerHeight,
			0.1,
			1000
		);

		const controls = new OrbitControls(camera, canvas);
		controls.update();
		const renderer = new THREE.WebGLRenderer({
			canvas,
			antialias: true
		});
		// Add event listeners for keyboard controls
		document.addEventListener('keydown', onKeyDown);
		document.addEventListener('keyup', onKeyUp);

		const keys = {
			LEFT: 'KeyA',
			UP: 'KeyW',
			RIGHT: 'KeyD',
			DOWN: 'KeyS'
		};

		let movement = {
			forward: false,
			backward: false,
			left: false,
			right: false
		};

		function onKeyDown(event: { code: any }) {
			switch (event.code) {
				case keys.UP:
					movement.forward = true;
					break;
				case keys.DOWN:
					movement.backward = true;
					break;
				case keys.LEFT:
					movement.left = true;
					break;
				case keys.RIGHT:
					movement.right = true;
					break;
			}
		}

		function onKeyUp(event: { code: any }) {
			switch (event.code) {
				case keys.UP:
					movement.forward = false;
					break;
				case keys.DOWN:
					movement.backward = false;
					break;
				case keys.LEFT:
					movement.left = false;
					break;
				case keys.RIGHT:
					movement.right = false;
					break;
			}
		}

		renderer.setSize(window.innerWidth, window.innerHeight);
		renderer.setClearColor(0x000000);
		let proximityThreshold = 25; // Distance threshold for clustering

		const clusters = []; // Array to store cluster indices

		// Assign a cluster index to each cube based on proximity
		console.log(result);
		for (let i = 0; i < result.length; i++) {
			const position = new THREE.Vector3(result[i][0] * 20, result[i][1] * 20, result[i][2] * 20);
			let clusterIndex = -1;

			// Check if the cube is close to any existing cluster
			for (let j = 0; j < clusters.length; j++) {
				const clusterPosition = scene.children[clusters[j]].position;
				// Compare the distance between the cube and the cluster's centroid
				if (position.distanceTo(clusterPosition) <= proximityThreshold) {
					clusterIndex = clusters[j];
					break;
				}
			}

			// If no nearby cluster found, create a new cluster
			if (clusterIndex === -1) {
				clusterIndex = scene.children.length;
				clusters.push(clusterIndex);
			}

			// Create the cube and assign a color based on the cluster index
			const geometry = new THREE.BoxGeometry(1, 1, 1);
			const material = new THREE.MeshBasicMaterial({
				color: new THREE.Color().setHSL(clusterIndex / clusters.length, 1, 0.5)
			});

			const cube = new THREE.Mesh(geometry, material);
			cube.name = Object.keys(data)[i];
			cube.position.copy(position);
			scene.add(cube);
		}

		camera.position.z = 75;

		const animate = function () {
			requestAnimationFrame(animate);

			// Move the camera based on keyboard input
			const moveSpeed = 10;
			if (movement.forward) {
				camera.position.z -= moveSpeed;
			}
			if (movement.backward) {
				camera.position.z += moveSpeed;
			}
			if (movement.left) {
				camera.position.x -= moveSpeed;
			}
			if (movement.right) {
				camera.position.x += moveSpeed;
			}

			// Update the controls
			controls.update();

			// Render the scene
			renderer.render(scene, camera);
		};

		animate();
		document.addEventListener('mousemove', onMouseMove);
		document.addEventListener('mouseleave', onMouseLeave);

		function onMouseMove(event: { clientX: number; clientY: number }) {
			// Calculate normalized device coordinates
			mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
			mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

			// Perform raycasting to check intersection with cubes
			raycaster.setFromCamera(mouse, camera);
			const intersects = raycaster.intersectObjects(scene.children);

			// Check if any cube is being hovered
			if (intersects.length > 0) {
				const intersectedObject = intersects[0].object;

				// Retrieve metadata for the hovered cube
				const cubeName = intersectedObject.name;
				const cubeData = data[cubeName];
				console.log(cubeData);
				thread_id_num = cubeName;
				chat_data = cubeData.chat;
				// outline the cube only on hover
				if (outlinedObjects.length > 1) {
					outlinedObjects[0][0].material = outlinedObjects[0][1];
					outlinedObjects.shift();
				}
				let prevMaterial = intersectedObject.material;
				intersectedObject.material = new THREE.MeshBasicMaterial({
					color: 0xffffff,
					wireframe: true
				});
				outlinedObjects.push([intersectedObject, prevMaterial]);
			}
		}

		function onMouseLeave() {
			// Clear the displayed metadata when the mouse leaves the canvas
			console.log('Mouse left the canvas');
		}
	};
	onMount(() => {
		// read the data from the text file
		fetch('embeddings.txt')
			.then((res) => {
				console.log(res);
				console.log('res');
				return res.json();
			})
			.then((json) => {
				data = json;
				console.log('data');
				console.log(json);
				// json is the form of {id: {embedding: [], chat : ""}}
				for (let key in json) {
					let vector = json[key]['embedding'];
					let split = vector.replace('[', '').replace(']', '').split(',');
					vector = split.map((x: string) => parseFloat(x));
					coorddata.push(vector.map((x: string) => parseFloat(x)));
					// console.log(key);
				}
			})
			.then(() => {
				console.log('coorddata');
				console.log(coorddata);
				result = umap.fit(coorddata);
				let nEpochs = umap.initializeFit(coorddata);
				umap.getEmbedding();
				for (let i = 0; i < nEpochs; i++) {
					umap.step();
					console.log(i);
				}
				umap.getEmbedding();
				console.log(result);
			})
			.then(() => {
				console.log('resultAAAAAA');
				console.log(result);
				for (let key in data) {
					data[key]['embedding'] = result.shift();
				}
				console.log('AAAAAAA');
				for (let key in data) {
					result.push(data[key]['embedding']);
				}
				renderPoints(data);
			});
	});
</script>

<div class="w-screen h-screen">
	<canvas class="w-full h-full" bind:this={canvas} />
</div>

<div class="absolute bg-black text-white text-lg top-0 w-1/4 h-1/4 bg-opacity-50">
	<h1>Thread Id: {thread_id_num}</h1>
	<h1>Chat Data: {chat_data}</h1>
</div>
