document.addEventListener("DOMContentLoaded", function () {
    // Speed up keeper note WebM animation if present.
    var keeperVideos = document.querySelectorAll("video.keeper-note-sprite");
    keeperVideos.forEach(function (v) {
        var rate = 1.8;
        v.autoplay = true;
        v.loop = true;
        v.muted = true;
        v.playsInline = true;
        v.playbackRate = rate;
        v.addEventListener("loadedmetadata", function () {
            v.playbackRate = rate;
        });
    });

    // Try to focus the first field on the main forms so you can just start typing.
    var firstFormField = document.querySelector(
        ".rainforest-form input, .rainforest-form select, .rainforest-form textarea"
    );
    if (firstFormField && !firstFormField.hasAttribute("autofocus")) {
        firstFormField.focus();
    }

    // Fade cards up as they enter the viewport.
    var fadeItems = document.querySelectorAll(".fade-rise");
    if (fadeItems.length > 0 && "IntersectionObserver" in window) {
        var observer = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.1 }
        );
        fadeItems.forEach(function (el) {
            observer.observe(el);
        });
    }

    // Mini 3D viewer tilt used on various cards.
    var miniViewers = document.querySelectorAll(".mini-3d-viewer");
    miniViewers.forEach(function (viewer) {
        var body =
            viewer.querySelector(".mini-ant-body") ||
            viewer.querySelector(".keeper-note-sprite") ||
            viewer.firstElementChild;

        if (!body) {
            return;
        }

        function resetTilt() {
            body.style.transform = "rotateX(12deg) rotateY(-10deg)";
        }

        function handleMove(clientX, clientY) {
            var rect = viewer.getBoundingClientRect();
            if (!rect.width || !rect.height) {
                return;
            }

            var x = (clientX - rect.left) / rect.width;
            var y = (clientY - rect.top) / rect.height;
            var rotateY = (x - 0.5) * 30;
            var rotateX = (0.5 - y) * 24;
            body.style.transform =
                "rotateX(" + rotateX + "deg) rotateY(" + rotateY + "deg)";
        }

        viewer.addEventListener("mousemove", function (event) {
            handleMove(event.clientX, event.clientY);
        });

        viewer.addEventListener("mouseleave", resetTilt);

        viewer.addEventListener("touchmove", function (event) {
            if (event.touches && event.touches.length > 0) {
                var touch = event.touches[0];
                handleMove(touch.clientX, touch.clientY);
            }
        });

        viewer.addEventListener("touchend", resetTilt);

        resetTilt();
    });

    // Flight map positioning, driven by the JSON API.
    var map = document.getElementById("flight-map");
    if (map) {
        var tableBody = document.querySelector("[data-flight-table-body]");
        var markers = [];

        function positionMarkers() {
            var width = map.clientWidth;
            var height = map.clientHeight;
            if (!width || !height || !markers.length) {
                return;
            }

            markers.forEach(function (marker) {
                var lat = parseFloat(marker.dataset.lat);
                var lng = parseFloat(marker.dataset.lng);
                if (isNaN(lat) || isNaN(lng)) {
                    return;
                }

                // Simple "good enough" projection to spread markers over the image.
                var x = ((lng + 180) / 360) * width;
                var y = ((90 - lat) / 180) * height;

                marker.style.left = x + "px";
                marker.style.top = y + "px";
            });
        }

        function renderFlights(flights) {
            // Clear previous markers.
            markers.splice(0, markers.length);

            var overlay = map.querySelector(".flight-map-overlay");
            map.innerHTML = "";
            if (overlay) {
                map.appendChild(overlay);
            }

            flights.forEach(function (flight) {
                if (flight.latitude == null || flight.longitude == null) {
                    return;
                }
                var marker = document.createElement("div");
                marker.className = "flight-marker";
                marker.dataset.lat = flight.latitude;
                marker.dataset.lng = flight.longitude;
                marker.title =
                    (flight.species_name || "Unknown species") +
                    " at " +
                    (flight.location_name || "Unknown location") +
                    " on " +
                    (flight.date || "");
                map.appendChild(marker);
                markers.push(marker);
            });

            positionMarkers();

            if (tableBody) {
                tableBody.innerHTML = "";
                if (!flights.length) {
                    var row = document.createElement("tr");
                    var cell = document.createElement("td");
                    cell.colSpan = 5;
                    cell.textContent = "No flights recorded yet.";
                    row.appendChild(cell);
                    tableBody.appendChild(row);
                } else {
                    flights.forEach(function (flight) {
                        var row = document.createElement("tr");

                        var dateCell = document.createElement("td");
                        dateCell.textContent = flight.date || "";
                        row.appendChild(dateCell);

                        var speciesCell = document.createElement("td");
                        if (flight.species_slug) {
                            var link = document.createElement("a");
                            link.href = "/species/" + flight.species_slug + "/";
                            link.textContent =
                                flight.species_name || "Unknown species";
                            link.className = "link-light";
                            speciesCell.appendChild(link);
                        } else {
                            speciesCell.textContent =
                                flight.species_name || "Unknown species";
                        }
                        row.appendChild(speciesCell);

                        var locationCell = document.createElement("td");
                        locationCell.textContent = flight.location_name || "";
                        row.appendChild(locationCell);

                        var regionCell = document.createElement("td");
                        regionCell.textContent = flight.region || "";
                        row.appendChild(regionCell);

                        var reporterCell = document.createElement("td");
                        reporterCell.textContent =
                            flight.reporter || "Anonymous";
                        row.appendChild(reporterCell);

                        tableBody.appendChild(row);
                    });
                }
            }
        }

        function loadFlightsFromApi() {
            var params = new URLSearchParams(window.location.search);
            var apiParams = new URLSearchParams();
            var species = params.get("species");
            var region = params.get("region");
            if (species) {
                apiParams.set("species", species);
            }
            if (region) {
                apiParams.set("region", region);
            }
            apiParams.set("limit", "500");

            fetch("/api/flights/?" + apiParams.toString())
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error("Failed to load flights API");
                    }
                    return response.json();
                })
                .then(function (data) {
                    var flights = (data && data.results) || [];
                    renderFlights(flights);
                })
                .catch(function (error) {
                    console.error(error);
                });
        }

        window.addEventListener("resize", positionMarkers);
        loadFlightsFromApi();
    }

    // ---------------------------------------------------------------------
    // Roaming ants in the background – smarter, stateful behavior + dragging.
    // ---------------------------------------------------------------------
    var antLayer = document.getElementById("ant-scout-layer");
    if (antLayer) {
        var videoSrc =
            antLayer.getAttribute("data-ant-video-src") ||
            antLayer.getAttribute("data-ant-gif-src") ||
            antLayer.getAttribute("data-ant-gif") ||
            "";

        if (videoSrc) {
            var ANT_COUNT = 14;
            var ANT_SIZE = 64;
            var ants = [];
            var margin = 40;
            var draggingAnt = null;
            var dragOffsetX = 0;
            var dragOffsetY = 0;
            var lastTime = performance.now();

            function spawnAnt() {
                var video = document.createElement("video");
                video.className = "ant-scout";
                video.src = videoSrc;
                video.autoplay = true;
                video.loop = true;
                video.muted = true;
                video.playsInline = true;

                var targetRate = 1.8;
                video.playbackRate = targetRate;
                video.addEventListener("loadedmetadata", function () {
                    video.playbackRate = targetRate;
                });

                // keep ants in the background layer
                antLayer.appendChild(video);

                var width =
                    window.innerWidth ||
                    document.documentElement.clientWidth;
                var height =
                    window.innerHeight ||
                    document.documentElement.clientHeight;

                var x;
                var y;
                var angle;

                var edgeRoll = Math.random();
                if (edgeRoll < 0.25) {
                    x = Math.random() * width;
                    y = -margin;
                    angle = 70 + Math.random() * 40;
                } else if (edgeRoll < 0.5) {
                    x = Math.random() * width;
                    y = height + margin;
                    angle = -110 + Math.random() * 40;
                } else if (edgeRoll < 0.75) {
                    x = -margin;
                    y = Math.random() * height;
                    angle = -20 + Math.random() * 40;
                } else {
                    x = width + margin;
                    y = Math.random() * height;
                    angle = 160 + Math.random() * 40;
                }

                var speed = 110 + Math.random() * 80;

                var ant = {
                    el: video,
                    x: x,
                    y: y,
                    angle: angle,
                    speed: speed,
                    isDragging: false,
                    mood: "wander",
                    decisionTimer: 0,
                    decisionInterval: 0.75 + Math.random() * 1.25,
                    wanderBias: (Math.random() - 0.5) * 0.4
                };

                ants.push(ant);
                return ant;
            }

            for (var i = 0; i < ANT_COUNT; i++) {
                spawnAnt();
            }

            // Find nearest ant to click point.
            function findAntAt(clientX, clientY) {
                var best = null;
                var bestDistSq = Infinity;
                var half = ANT_SIZE / 2;

                ants.forEach(function (ant) {
                    var dx = clientX - ant.x;
                    var dy = clientY - ant.y;

                    if (Math.abs(dx) > half || Math.abs(dy) > half) {
                        return;
                    }

                    var d2 = dx * dx + dy * dy;
                    if (d2 < bestDistSq) {
                        bestDistSq = d2;
                        best = ant;
                    }
                });

                return best;
            }

            function startDragPointer(clientX, clientY) {
                var ant = findAntAt(clientX, clientY);
                if (!ant) {
                    return false;
                }
                draggingAnt = ant;
                ant.isDragging = true;
                dragOffsetX = clientX - ant.x;
                dragOffsetY = clientY - ant.y;
                ant.el.classList.add("ant-is-dragging");
                return true;
            }

            // Capture phase so we see events even if foreground elements are on top.
            document.addEventListener(
                "mousedown",
                function (event) {
                    var started = startDragPointer(
                        event.clientX,
                        event.clientY
                    );
                    if (started) {
                        event.preventDefault();
                    }
                },
                true
            );

            document.addEventListener(
                "touchstart",
                function (event) {
                    if (!event.touches || event.touches.length === 0) {
                        return;
                    }
                    var touch = event.touches[0];
                    var started = startDragPointer(
                        touch.clientX,
                        touch.clientY
                    );
                    if (started) {
                        event.preventDefault();
                    }
                },
                true
            );

            function updateDraggingPosition(clientX, clientY) {
                if (!draggingAnt) {
                    return;
                }

                var width =
                    window.innerWidth ||
                    document.documentElement.clientWidth;
                var height =
                    window.innerHeight ||
                    document.documentElement.clientHeight;

                var newX = clientX - dragOffsetX;
                var newY = clientY - dragOffsetY;

                if (newX < -margin) newX = -margin;
                if (newX > width + margin) newX = width + margin;
                if (newY < -margin) newY = -margin;
                if (newY > height + margin) newY = height + margin;

                draggingAnt.x = newX;
                draggingAnt.y = newY;

                draggingAnt.el.style.transform =
                    "translate(" +
                    draggingAnt.x +
                    "px, " +
                    draggingAnt.y +
                    "px) rotate(" +
                    (draggingAnt.angle + 90) +
                    "deg) scale(1.1)";
            }

            function stopDragging() {
                if (!draggingAnt) {
                    return;
                }
                draggingAnt.isDragging = false;
                draggingAnt.el.classList.remove("ant-is-dragging");
                draggingAnt = null;
            }

            document.addEventListener("mousemove", function (event) {
                if (!draggingAnt) {
                    return;
                }
                event.preventDefault();
                updateDraggingPosition(event.clientX, event.clientY);
            });

            document.addEventListener("touchmove", function (event) {
                if (
                    !draggingAnt ||
                    !event.touches ||
                    event.touches.length === 0
                ) {
                    return;
                }
                var touch = event.touches[0];
                updateDraggingPosition(touch.clientX, touch.clientY);
            });

            document.addEventListener("mouseup", function () {
                stopDragging();
            });

            document.addEventListener("touchend", function () {
                stopDragging();
            });

            function step(now) {
                var width =
                    window.innerWidth ||
                    document.documentElement.clientWidth;
                var height =
                    window.innerHeight ||
                    document.documentElement.clientHeight;

                var dt = Math.min((now - lastTime) / 1000, 0.05);
                lastTime = now;

                var nestX = width * 0.5;
                var nestY = height * 0.85;

                ants.forEach(function (ant, idx) {
                    if (ant.isDragging) {
                        return;
                    }

                    ant.decisionTimer += dt;

                    if (ant.decisionTimer > ant.decisionInterval) {
                        ant.decisionTimer = 0;
                        ant.decisionInterval =
                            0.75 + Math.random() * 1.25;

                        var dxNest0 = nestX - ant.x;
                        var dyNest0 = nestY - ant.y;
                        var distNestSq0 = dxNest0 * dxNest0 + dyNest0 * dyNest0;

                        if (
                            distNestSq0 > 200 * 200 &&
                            Math.random() < 0.25
                        ) {
                            ant.mood = "return";
                        } else if (Math.random() < 0.3) {
                            ant.mood = "wander";
                        }

                        ant.angle += (Math.random() - 0.5) * 40;
                    }

                    var dirX = Math.cos((ant.angle * Math.PI) / 180);
                    var dirY = Math.sin((ant.angle * Math.PI) / 180);

                    var bias = ant.wanderBias;
                    if (bias !== 0) {
                        var oldX = dirX;
                        dirX = dirX - dirY * bias;
                        dirY = dirY + oldX * bias;
                    }

                    var edgeSteerX = 0;
                    var edgeSteerY = 0;
                    var safeMargin = margin + 20;

                    if (ant.x < safeMargin) {
                        edgeSteerX += 1;
                    }
                    if (ant.x > width - safeMargin) {
                        edgeSteerX -= 1;
                    }
                    if (ant.y < safeMargin) {
                        edgeSteerY += 1;
                    }
                    if (ant.y > height - safeMargin) {
                        edgeSteerY -= 1;
                    }

                    dirX += edgeSteerX * 2.5;
                    dirY += edgeSteerY * 2.5;

                    var sepX = 0;
                    var sepY = 0;
                    var desiredSep = 70;
                    var desiredSepSq = desiredSep * desiredSep;

                    for (var j = 0; j < ants.length; j++) {
                        if (j === idx) continue;
                        var other = ants[j];
                        if (other.isDragging) continue;

                        var dx = ant.x - other.x;
                        var dy = ant.y - other.y;
                        var d2 = dx * dx + dy * dy;
                        if (d2 > 0 && d2 < desiredSepSq) {
                            var inv = 1 / Math.sqrt(d2);
                            sepX += dx * inv;
                            sepY += dy * inv;
                        }
                    }

                    dirX += sepX * 1.5;
                    dirY += sepY * 1.5;

                    var dxNest = nestX - ant.x;
                    var dyNest = nestY - ant.y;
                    var distNestSq = dxNest * dxNest + dyNest * dyNest;
                    if (ant.mood === "return" && distNestSq > 80 * 80) {
                        var invNest =
                            1 / Math.max(Math.sqrt(distNestSq), 1);
                        dirX += dxNest * invNest * 1.8;
                        dirY += dyNest * invNest * 1.8;
                    }

                    if (dirX === 0 && dirY === 0) {
                        dirX = Math.cos((ant.angle * Math.PI) / 180);
                        dirY = Math.sin((ant.angle * Math.PI) / 180);
                    }

                    var len = Math.sqrt(dirX * dirX + dirY * dirY);
                    if (len > 0.0001) {
                        dirX /= len;
                        dirY /= len;
                    }

                    var newAngle =
                        (Math.atan2(dirY, dirX) * 180) / Math.PI;
                    var maxTurn = 160 * dt;
                    var delta =
                        ((newAngle - ant.angle + 540) % 360) - 180;
                    if (delta > maxTurn) delta = maxTurn;
                    if (delta < -maxTurn) delta = -maxTurn;
                    ant.angle += delta;

                    var rad = (ant.angle * Math.PI) / 180;
                    var distance = ant.speed * dt;
                    ant.x += Math.cos(rad) * distance;
                    ant.y += Math.sin(rad) * distance;

                    if (ant.x < -margin) ant.x = -margin;
                    if (ant.x > width + margin) ant.x = width + margin;
                    if (ant.y < -margin) ant.y = -margin;
                    if (ant.y > height + margin) ant.y = height + margin;

                    ant.el.style.transform =
                        "translate(" +
                        ant.x +
                        "px, " +
                        ant.y +
                        "px) rotate(" +
                        (ant.angle + 90) +
                        "deg)";
                });

                window.requestAnimationFrame(step);
            }

            window.requestAnimationFrame(step);

            window.addEventListener("resize", function () {
                var width =
                    window.innerWidth ||
                    document.documentElement.clientWidth;
                var height =
                    window.innerHeight ||
                    document.documentElement.clientHeight;

                ants.forEach(function (ant) {
                    ant.x = Math.max(
                        -margin,
                        Math.min(width + margin, ant.x)
                    );
                    ant.y = Math.max(
                        -margin,
                        Math.min(height + margin, ant.y)
                    );
                });
            });
        }
    }
});
