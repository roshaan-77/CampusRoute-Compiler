map center=(24.8586, 67.1672) zoom=11 theme=light

let mainCampus = (24.857468, 67.264638)
let cityCampus = (24.859722, 67.069722)
let startCampus = mainCampus
let endCampus = cityCampus

layer "FAST Campuses"
    marker "FAST NUCES Karachi Main Campus" at startCampus color=blue icon=school
    marker "FAST NUCES Karachi City Campus" at endCampus color=red icon=school
end

route "FAST Main Campus to FAST City Campus"
    from startCampus
    to   endCampus
    color=orange width=3
end

circle at startCampus radius=250m color=blue opacity=0.2
circle at endCampus radius=250m color=green opacity=0.2

label "Saddar" at (24.8550, 67.0100) size=medium color=black
label "Defence" at (24.8080, 67.0580) size=medium color=black
label "Johar" at (24.911949, 67.125683) size=medium color=black
label "Gulshan" at (24.918412, 67.097854) size=medium color=black

if zoom >= 12 then
    label "KPT" at (24.8400, 67.0050) size=medium color=red
end

let busstops = [(24.886818, 67.143210), (24.884450, 67.174809), (24.855262, 67.211637), (24.854985, 67.228638)]

layer "Bus Stops"
    for stop in busstops
        marker "Bus Stop" at stop color=purple icon=dot
    end
end

export as "fast_campus_distance.html"
