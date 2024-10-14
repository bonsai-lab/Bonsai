let updateInterval;
let volatilityUpdateInterval;
let ivSkewUpdateInterval;
let isSurfacePaused = false;
let isVolatilityPaused = false;
let isIvSkewPaused = false;
let isIvTermStructurePaused = false;
let zIndexCounter = 4; // Start z-index counter at 4 to account for 4 plots

// Function to fetch the updated plot
function fetchUpdatedPlot() {
    $.ajax({
        type: 'POST',
        url: '/update_plot',
        success: function(response) {
            if (response.plot_html) {
                $('#surface-plot-container').html(response.plot_html);
                if (response.plot_data) {
                    Plotly.react('surface-plot-container', JSON.parse(response.plot_data));
                }
            }
        },
        error: function() {
            console.error('Failed to update the surface plot.');
        }
    });
}

// Function to fetch the updated volatility plot
function fetchUpdatedVolatilityPlot() {
    $.ajax({
        type: 'POST',
        url: '/update_volatility_plot',
        success: function(response) {
            if (response.volatility_plot_html) {
                $('#volatility-plot-container').html(response.volatility_plot_html);
                if (response.volatility_plot_data) {
                    Plotly.react('volatility-plot-container', JSON.parse(response.volatility_plot_data));
                }
            }
        },
        error: function() {
            console.error('Failed to update the volatility plot.');
        }
    });
}



function fetchUpdatedIvSkewPlot() {
    $.ajax({
        type: 'POST',
        url: '/update_iv_skew_plot',
        data: { search: searchQuery },  
        success: function(response) {
            if (response.iv_skew_plot_html) {
                $('#iv-skew-plot-container').html(response.iv_skew_plot_html);
                if (response.iv_skew_plot_data) {
                    Plotly.react('iv-skew-plot-container', JSON.parse(response.iv_skew_plot_data));
                }
            }
        },
        error: function() {
            console.error('Failed to update the IV skew plot.');
        }
    });
}



function fetchUpdatedIvTermStructurePlot() {
    $.ajax({
        type: 'POST',
        url: '/update_iv_term_structure_plot',  // Updated URL
        data: { search: searchQuery },  
        success: function(response) {
            if (response.iv_term_structure_plot_html) {  // Updated key
                $('#iv-term-structure-plot-container').html(response.iv_term_structure_plot_html);  // Updated container ID
                if (response.iv_term_structure_plot_data) {  // Updated key
                    Plotly.react('iv-term-structure-plot-container', JSON.parse(response.iv_term_structure_plot_data));
                }
            }
        },
        error: function() {
            console.error('Failed to update the IV term structure plot.');  // Updated error message
        }
    });
}


function fetchUpdatedWsOutput() {
    $.ajax({
        type: 'POST',
        url: '/search',  
        data: { search: searchQuery }, 
        success: function(response) {
            console.log('WebSocket Update Response:', response.result);

            // Update the #ws-output-container
            $('#ws-output-container').html(formatResponse(response.result));

            // Update the navbar placeholders with WebSocket data
            let indexPrice = response.result.index_price !== null ? response.result.index_price.toFixed(2) : '--';
            let highPrice = response.result.stats?.high !== null ? response.result.stats.high.toFixed(2) : '--';
            let lowPrice = response.result.stats?.low !== null ? response.result.stats.low.toFixed(2) : '--';

            $('#index-price').text(` ${indexPrice}`);
            $('#high-price').text(` ${highPrice}`);
            $('#low-price').text(` ${lowPrice}`);
        },
        error: function() {
            console.error('Failed to update WebSocket output.');
            $('#ws-output-container').html('Error: Unable to fetch WebSocket data.');
        }
    });
}



let wsUpdateInterval;
let isWsPaused = false;

// Start automatic updates for WebSocket output
function startAutomaticWsUpdates() {
    wsUpdateInterval = setInterval(fetchUpdatedWsOutput, 5000);  // Update every 5 seconds
    $('#pause-resume-ws-btn').text('Online').removeClass('btn-secondary').addClass('btn-primary');
    isWsPaused = false;
}

// Stop automatic updates for WebSocket output
function stopAutomaticWsUpdates() {
    clearInterval(wsUpdateInterval);
    $('#pause-resume-ws-btn').text('Offline').removeClass('btn-primary').addClass('btn-secondary');
    isWsPaused = true;
}


// Start automatic updates for surface plot
function startAutomaticSurfaceUpdates() {
    updateInterval = setInterval(fetchUpdatedPlot, 10000); // Update every X ms
    $('#pause-resume-surface-btn').text('Online').removeClass('btn-secondary').addClass('btn-primary');
    isSurfacePaused = false;
}

// ... for volatility plot
function startAutomaticVolatilityUpdates() {
    volatilityUpdateInterval = setInterval(fetchUpdatedVolatilityPlot, 5000); // Update every X ms
    $('#pause-resume-volatility-btn').text('Online').removeClass('btn-secondary').addClass('btn-primary');
    isVolatilityPaused = false;
}

// ... for IV skew plot
function startAutomaticIvSkewUpdates() {
    ivSkewUpdateInterval = setInterval(fetchUpdatedIvSkewPlot, 2200); // Update every X ms
    $('#pause-resume-iv-skew-btn').text('Online').removeClass('btn-secondary').addClass('btn-primary');
    isIvSkewPaused = false;
}

// ... for IV term structure plot
function startAutomaticIvTermStructureUpdates() {
    ivTermStructureUpdateInterval = setInterval(fetchUpdatedIvTermStructurePlot, 2000); // Update every X ms
    $('#pause-resume-iv-term-structure-btn').text('Online').removeClass('btn-secondary').addClass('btn-primary');
    isIvTermStructurePaused = false;
}



// Stop automatic updates for surface plot
function stopAutomaticSurfaceUpdates() {
    clearInterval(updateInterval);
    $('#pause-resume-surface-btn').text('Offline').removeClass('btn-primary').addClass('btn-secondary');
    isSurfacePaused = true;
}

// ... for volatility plot
function stopAutomaticVolatilityUpdates() {
    clearInterval(volatilityUpdateInterval);
    $('#pause-resume-volatility-btn').text('Offline').removeClass('btn-primary').addClass('btn-secondary');
    isVolatilityPaused = true;
}

// ... for IV skew plot
function stopAutomaticIvSkewUpdates() {
    clearInterval(ivSkewUpdateInterval);
    $('#pause-resume-iv-skew-btn').text('Offline').removeClass('btn-primary').addClass('btn-secondary');
    isIvSkewPaused = true;
}


// ... for IV term structure plot
function stopAutomaticIvTermStructureUpdates() {
    clearInterval(ivTermStructureUpdateInterval); // Use the correct interval variable
    $('#pause-resume-iv-term-structure-btn').text('Offline').removeClass('btn-primary').addClass('btn-secondary');
    isIvTermStructurePaused = true;

}

// Toggle pause/resume for surface plot
$('#pause-resume-surface-btn').on('click', function() {
    if (isSurfacePaused) {
        startAutomaticSurfaceUpdates();
    } else {
        stopAutomaticSurfaceUpdates();
    }
});

// Toggle pause/resume for volatility plot
$('#pause-resume-volatility-btn').on('click', function() {
    if (isVolatilityPaused) {
        startAutomaticVolatilityUpdates();
    } else {
        stopAutomaticVolatilityUpdates();
    }
});

// Toggle pause/resume for IV skew plot
$('#pause-resume-iv-skew-btn').on('click', function() {
    if (isIvSkewPaused) {
        startAutomaticIvSkewUpdates();
    } else {
        stopAutomaticIvSkewUpdates();
    }
});


// Toggle pause/resume for IV skew plot
$('#pause-resume-iv-term-structure-btn').on('click', function() {
    if (isIvTermStructurePaused) {
        startAutomaticIvTermStructureUpdates();
    } else {
        stopAutomaticIvTermStructureUpdates();
    }
});

$(document).ready(function() {
    startAutomaticSurfaceUpdates();
    startAutomaticVolatilityUpdates();
    startAutomaticIvSkewUpdates();
    startAutomaticIvTermStructureUpdates();
    startAutomaticWsUpdates();  // Start WebSocket updates automatically

    fetchUpdatedPlot();  // Fetch surface plot immediately on page load
    fetchUpdatedVolatilityPlot();  // Fetch volatility plot immediately on page load
    fetchUpdatedIvSkewPlot();  // Fetch IV skew plot immediately on page load
    fetchUpdatedIvTermStructurePlot();
    fetchUpdatedWsOutput();  // Fetch WebSocket data immediately on page load
});


// Drag and resize functionality
function enableDragAndResize(wrapperId, headerId, handleId) {
    const plotWrapper = document.getElementById(wrapperId);
    const plotHeader = document.getElementById(headerId);
    const resizeHandle = document.getElementById(handleId);
    let isResizing = false;
    let isDragging = false;
    let startX = 0;
    let startY = 0;
    let startLeft = 0;
    let startTop = 0;
    let startWidth = 0;
    let startHeight = 0;

    // Drag logic
    plotHeader.addEventListener('mousedown', (e) => {
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        startLeft = plotWrapper.offsetLeft;
        startTop = plotWrapper.offsetTop;
        plotWrapper.style.zIndex = zIndexCounter++;
    });

    document.addEventListener('mousemove', (e) => {
        if (isDragging) {
            const deltaX = e.clientX - startX;
            const deltaY = e.clientY - startY;
            plotWrapper.style.left = `${startLeft + deltaX}px`;
            plotWrapper.style.top = `${startTop + deltaY}px`;
        }
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
    });

    // Resize logic
    resizeHandle.addEventListener('mousedown', (e) => {
        isResizing = true;
        startX = e.clientX;
        startY = e.clientY;
        startWidth = plotWrapper.offsetWidth;
        startHeight = plotWrapper.offsetHeight;
        e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
        if (isResizing) {
            const deltaX = e.clientX - startX;
            const deltaY = e.clientY - startY;
            plotWrapper.style.width = `${startWidth + deltaX}px`;
            plotWrapper.style.height = `${startHeight + deltaY}px`;
        }
    });

    document.addEventListener('mouseup', () => {
        isResizing = false;
    });
}



let searchQuery = '';  // Global variable to store the search query

// Search bar functionality to update searchQuery when Enter is pressed
$(document).ready(function() {
    $('#searchInput').on('keypress', function(e) {
        // Check if the pressed key is Enter (keyCode 13)
        if (e.which === 13) {
            e.preventDefault();  // Prevent the default behavior

            searchQuery = $(this).val().trim();  // Store the search query in the global variable

            if (searchQuery !== "") {
                // Send the search query to the backend via AJAX
                $.ajax({
                    type: 'POST',
                    url: '/search',
                    data: { search: searchQuery },
                    success: function(response) {
                        console.log('WebSocket Response:', response.result);

                        // Format and display the result in the #ws-output-container
                        $('#ws-output-container').html(formatResponse(response.result));
                    },
                    error: function() {
                        console.error('Search request failed.');
                        $('#ws-output-container').html('Error: Unable to fetch data from WebSocket.');
                    }
                });
            }
        }
    });
});


function formatResponse(data) {
    if (data.error) {
        return `<p>Error: ${data.error}</p>`;
    }

    // Create the table HTML
    let html = `
        <table class="ws-table">
            <thead>
                <tr>
                    <th>Key</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
                <tr><td>Instrument Name</td><td>${data.instrument_name || 'N/A'}</td></tr>
                <tr><td>Underlying Price</td><td>${data.underlying_price !== null ? data.underlying_price.toFixed(2) : 'N/A'}</td></tr>
                <tr><td>Index Price</td><td>${data.index_price !== null ? data.index_price.toFixed(2) : 'N/A'}</td></tr>
                <tr><td>Last Price</td><td>${data.last_price !== null ? data.last_price.toFixed(4) : 'N/A'}</td></tr>
                <tr><td>Mark Price</td><td>${data.mark_price !== null ? data.mark_price.toFixed(4) : 'N/A'}</td></tr>
                <tr><td>Open Interest</td><td>${data.open_interest !== null ? data.open_interest.toFixed(2) : 'N/A'}</td></tr>
                <tr><td>Best Bid Price</td><td>${data.best_bid_price !== null ? data.best_bid_price.toFixed(4) : 'N/A'}</td></tr>
                <tr><td>Best Ask Price</td><td>${data.best_ask_price !== null ? data.best_ask_price.toFixed(4) : 'N/A'}</td></tr>
                <tr><td>Best Bid Amount</td><td>${data.best_bid_amount !== null ? data.best_bid_amount.toFixed(2) : 'N/A'}</td></tr>
                <tr><td>Best Ask Amount</td><td>${data.best_ask_amount !== null ? data.best_ask_amount.toFixed(2) : 'N/A'}</td></tr>
                <tr><td>Delta</td><td>${data.greeks?.delta !== null ? data.greeks.delta.toFixed(4) : 'N/A'}</td></tr>
                <tr><td>Gamma</td><td>${data.greeks?.gamma !== null ? data.greeks.gamma.toFixed(6) : 'N/A'}</td></tr>
                <tr><td>Theta</td><td>${data.greeks?.theta !== null ? data.greeks.theta.toFixed(4) : 'N/A'}</td></tr>
                <tr><td>Vega</td><td>${data.greeks?.vega !== null ? data.greeks.vega.toFixed(4) : 'N/A'}</td></tr>
                <tr><td>Rho</td><td>${data.greeks?.rho !== null ? data.greeks.rho.toFixed(4) : 'N/A'}</td></tr>
                <tr><td>High</td><td>${data.stats?.high !== null ? data.stats.high.toFixed(4) : 'N/A'}</td></tr>
                <tr><td>Low</td><td>${data.stats?.low !== null ? data.stats.low.toFixed(4) : 'N/A'}</td></tr>
                <tr><td>Price Change</td><td>${data.stats?.price_change !== null ? data.stats.price_change.toFixed(2) : 'N/A'}</td></tr>
                <tr><td>Volume</td><td>${data.stats?.volume !== null ? data.stats.volume.toFixed(2) : 'N/A'}</td></tr>
                <tr><td>Volume USD</td><td>${data.stats?.volume_usd !== null ? data.stats.volume_usd.toFixed(2) : 'N/A'}</td></tr>
            </tbody>
        </table>
    `;
    
    return html;
}


// Function to handle minimizing the entire plot window
function enableWindowMinimizing(wrapperId, btnId) {
    const minimizeButton = document.getElementById(btnId);
    const plotWrapper = document.getElementById(wrapperId);
    
    minimizeButton.addEventListener('click', () => {
        // Toggle the 'minimized' class which hides the window
        if (plotWrapper.classList.contains('minimized')) {
            plotWrapper.classList.remove('minimized');
            minimizeButton.textContent = '_'; // Update the button label to "_"
        } else {
            plotWrapper.classList.add('minimized');
            minimizeButton.textContent = '+'; // Update the button label to "+"
        }
    });
}





const menuBarHeight = 66; // Adjust this value based on your actual menu bar height

function setPlotDimensions() {
    const totalHeight = window.innerHeight - menuBarHeight; // Subtract the menu bar height
    const plotHeight = totalHeight / 2; // Divide height for 2 rows
    const plotWidth = (window.innerWidth - 300) / 2; // Remaining width for 2 plots

    // Set dimensions for each plot
    $('.plot-wrapper').css({
        width: `${plotWidth}px`,
        height: `${plotHeight}px`,
        margin: '0px',
        padding: '0',
        position: 'absolute'
    });

    // Position plots in two rows
    $('#volatility-plot-wrapper').css({ left: '0', top: '0' });
    $('#surface-plot-wrapper').css({ left: `${plotWidth}px`, top: '0' });
    $('#iv-skew-plot-wrapper').css({ left: '0', top: `${plotHeight}px` });
    $('#iv-term-structure-plot-wrapper').css({ left: `${plotWidth}px`, top: `${plotHeight}px` });
}

// Call the function on document ready and window resize
$(document).ready(setPlotDimensions);
$(window).resize(setPlotDimensions);



function setWsOutputDimensions() {
    const totalHeight = window.innerHeight - menuBarHeight; // Subtract the menu bar height

    $('#ws-output-wrapper').css({
        width: '300px', // Fixed width
        height: `${totalHeight}px`, // Full height minus menu bar
        margin: '0px',
        padding: '0',
        position: 'absolute',
        top: '0', // Align it to the top of the plots
        left: `${window.innerWidth - 300}px` // Position it to the right of the plots
    });
}

// Call this function similarly
$(document).ready(setWsOutputDimensions);
$(window).resize(setWsOutputDimensions);







// Enable minimizing for all windows
$(document).ready(function() {
    enableWindowMinimizing('volatility-plot-wrapper', 'minimize-volatility-btn');
    enableWindowMinimizing('surface-plot-wrapper', 'minimize-surface-btn');
    enableWindowMinimizing('iv-skew-plot-wrapper', 'minimize-iv-skew-btn');
    enableWindowMinimizing('iv-term-structure-plot-wrapper', 'minimize-iv-term-structure-btn');
    enableWindowMinimizing('ws-output-wrapper', 'minimize-ws-output-btn');
});


// Enable dragging and resizing for all plots
enableDragAndResize('volatility-plot-wrapper', 'volatility-plot-header', 'volatility-resize-handle');
enableDragAndResize('surface-plot-wrapper', 'surface-plot-header', 'surface-resize-handle');
enableDragAndResize('iv-skew-plot-wrapper', 'iv-skew-plot-header', 'iv-skew-resize-handle');
enableDragAndResize('iv-term-structure-plot-wrapper', 'iv-term-structure-plot-header', 'iv-term-structure-resize-handle');
enableDragAndResize('ws-output-wrapper', 'ws-output-header', 'ws-output-resize-handle');

















