/**
 * TheVirtualBrain-Framework Package. This package holds all Data Management, and 
 * Web-UI helpful to run brain-simulations. To use it, you also need do download
 * TheVirtualBrain-Scientific Package (for simulators). See content of the
 * documentation-folder for more details. See also http://www.thevirtualbrain.org
 *
 * (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
 *
 * This program is free software; you can redistribute it and/or modify it under 
 * the terms of the GNU General Public License version 2 as published by the Free
 * Software Foundation. This program is distributed in the hope that it will be
 * useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
 * License for more details. You should have received a copy of the GNU General 
 * Public License along with this program; if not, you can download it here
 * http://www.gnu.org/licenses/old-licenses/gpl-2.0
 *
 **/

/*

    tv.js should dump just a single public var named tv (T.VB V.isualizations)

        tv = {}

    with 

        tv.ndar     array fun
        tv.plot     reusable plotting components
        tv.util     utility stuff
        tv.save     save to canvas/png/svg src, etc. TODO


*/

tv = {}

tv.util = {

    // d3 style configurator. if this is slow, interp and eval source
    gen_access: function (obj, field) {
        return function(maybe) {
            if (maybe === undefined) {
                return obj["_" + field];
            } else {
                obj["_" + field] = maybe;
                return obj;
            }
        };
    }

    // helper to add usage notes to plots
    , usage: function (root, heading, notes)
      { var p = root.append("p")
        p.append("h3").classed("instructions", true).text(heading);
        p.append("ul").selectAll("li").data(notes)
            .enter().append("li").classed("instructions", true).text(function (d) {return d}); }

    , ord_nums : [ "zeroeth", "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth", "nineteenth" ]

    /* f is a templater/formatter cf. https://gist.github.com/984375 */
    , fmt: function (
            f // fhe format specifier
            // followed by any number of arguments
            ) {
        var a = arguments; // store outer arguments
        return ("" + f) // force format specifier to String
            .replace( // replace tokens in format specifier
                    /\{(?:(\d+)|(\w+))\}/g, // match {token} references
                    function (
                        s, // the matched string (ignored)
                        i, // an argument index
                        p // a property name
                        ) {
                    return p && a[1] // if property name and first argument exist
                    ? a[1][p] // return property from first argument
                    : a[i] // assume argument index and return i-th argument
                    })
    }

    , get_array_shape: function(baseURL, callback) {
        $.getJSON(baseURL + "/read_data_shape1/False?kwd=0", callback);
    }

    , get_array_slice: function(baseURL, slices, callback, channels) {
    	var readDataURL = readDataChannelURL(baseURL, slices[0].lo, slices[0].hi, null, null, slices[0].di, JSON.stringify(channels));
    	//NOTE: if we need to add slices for the other dimensions pass them as the 'specific_slices' parameter. Method called is from time_series_framework.py.
        $.getJSON(readDataURL , callback)
    }

}

tv.ndar = function (data) {

    this.data = data;

    this.imap = function(f) {
        for (var i=0; i<this.data.length; i++)
            this.data[i] = f(this.data[i]);
        return this;
    };

    this.map = function(f) {
        return (new tv.ndar(this.data.slice())).imap(f);
    };

    this.reduce = function(f, init) {
        for (var i=0; i<this.data.length; i++)
            init = f(init, this.data[i]);
        return init;
    };

    this.max = function() 
    { return this.reduce(function(l, r) { return l>r ? l : r; }, -1e300); };

    this.min = function()
    { return this.reduce(function(l, r) { return l<r ? l : r; },  1e300); };

    this.sum = function()
    { return this.reduce(function(l, r) { return l + r; }, 0); };

    this.mean = function()
    { return this.sum()/this.length(); };

    this.std = function()
    { var mean_sqr = this.map(function(x) { return x*x; }).mean(),
        mean = this.mean();
        return Math.sqrt( mean_sqr - mean*mean ); }; 

    this.add = function(b)
    { return this.map(function(x) { return x + b; }); };

    this.sub = function(b)
    { return this.add(-b); };

    this.mul = function(b)
    { return this.map(function(x) { return x * b; }); };

    this.imul = function(b)
    { return this.imap(function(x) { return x * b; }); };

    this.idiv = function(b)
    { return this.imul(1/b); };

    this.div = function(b)
    { return this.mul(1/b); };

    this.get = function(i)
    { return this.data[i]; };

    this.set = function(i, val)
    { this.data[i] = val; };

    this.nd2lin = function(idx)
    { var l = 0; 
        for (var i=0; i<idx.length; i++) l += this.strides[i]*idx[i];
        return l; };

    this.length = function() { return this.data.length; };

    // return indices where condition is true
    this.where = function(f) {
        var indices = [];
        for (var i=0; i<this.data.length; i++) {
            if (f(this.data[i], i)) { indices.push(i); }
        }
        return indices;
    }

    this.pretty_step = function(base)
    { return Math.pow(base, Math.floor(-1+Math.log(this.max() - this.min())/Math.log(base))); };

    this.pretty_ticks = function(base) 
    { var d = this.pretty_step(base || 10), f = Math.floor;
        return tv.ndar.range(f(this.min()/d)*d, (f(this.max()/d)+1)*d, d);};

    this.pretty_ticklabels = function(base)
    { return this.pretty_ticks(base).map(function(d) { return d.toPrecision(2); }); }

    this.normalized = function ()
    { var mn = this.min(), mx = this.max();
        return this.map(function(d) { return (d - mn)/(mx - mn); }); };

    this.slice = function(lo, hi)
    { return tv.ndar.from(this.data.slice(lo, hi)); }

}  

tv.ndar.from = function(src) { return new tv.ndar(src); }
tv.ndar.ndfrom = function(src) {
    var a = tv.ndar.from(src.data);
    a.shape = src.shape;
    a.strides = src.strides;
    return a;
}

tv.ndar.range = function(a, b, c) {
    var lo, hi, dx;

    if ((a || a===0) && b) {
        if (c) { dx = c; }
        else { dx = 1; }
        lo = a;
        hi = b;
    } else {
        hi = a;
        lo = 0;
        dx = 1;
    }

    var end = Math.floor((hi - lo)/dx);
    var ar = new tv.ndar([]);
    for (var i=0; i<end; i++) 
        ar.data[i] = dx*i + lo;
    return ar;

};  

tv.ndar.zeros = function(n) {
    return tv.ndar.range(n).imap(function(x) { return 0.0; }); 
};

tv.ndar.ones = function(n) {
    return tv.ndar.zeros(n).add(1.0);
};


tv.plot = {
    
    // reusable matrix plotter, supporting updates of data
    // TODO: selecting ranges on colorbar
    mat: function () {

        var f = function (root) {

            f.pad(f.pad() || 0.1);
            f.w  (  f.w() || 600);
            f.h  (  f.h() || 500);

            // inspect data
            var n = f.mat().shape[0]
              , m = f.mat().shape[1]
              
              ;

            // setup svg of config'd dims
            // var svg = root.append("svg").attr("width", f.w()).attr("heigh", f.h());

            var svg = root;
            
            // setup scales, axes and groups for matrix and colorbar
            var ma_sc_x = d3.scale.linear().domain([0, m]).range([0, f.w()*(1 - 4*f.pad())])
              , ma_sc_y = d3.scale.linear().domain([0, n]).range([0, f.h()*(1 - 2*f.pad())])
              , cb_sc_y = d3.scale.linear().domain([f.mat().max(), f.mat().min()])
                                            .range([0, f.h()*(1 - 2*f.pad())])
              , ma_sc_c = d3.scale.linear().domain([f.mat().min(), f.mat().max()]).range([0, 255]) // block color

              , ma_ax_x = d3.svg.axis().orient(  "top").scale(ma_sc_x)
              , ma_ax_y = d3.svg.axis().orient( "left").scale(ma_sc_y)
              , cb_ax_y = d3.svg.axis().orient("right").scale(cb_sc_y)

              , ma_gp   = svg.append("g").attr("transform", "translate(" + f.pad()*f.w() + ", " + f.h()*f.pad() + ")")
              , cb_gp   = svg.append("g").attr("transform", "translate(" + (f.w()*(1 - 2*f.pad())) + ", " + f.h()*f.pad() + ")")

              ;

            // plot matrix and its axes
            var ma_sz_x = f.w()*(1 - 4*f.pad())/m
              , ma_sz_y = f.h()*(1 - 2*f.pad())/n
              , ma_gp_rect_gp = ma_gp.append("g")

              , ma_gp_fill = function(d, i) { 
                var c = Math.floor(ma_sc_c(f.mat().data[i])); 
                return "rgb(" + c + ", 0, " + (255 - c) + ")"; 
            }

            ma_gp_rect_gp.selectAll("rect").data(f.mat().data).enter()
                .append("rect")
                .attr("fill", ma_gp_fill)
                .style("stroke", "transparent")
                .attr("x", function(d, i) { return ma_sz_x*(i % m); })
                .attr("y", function(d, i) { return ma_sz_y*Math.floor(i/m); })
                .attr("width",  ma_sz_x)
                .attr("height", ma_sz_y)
                .on("mouseover", f.mat_over() || function () {})

            ma_gp.append("g").attr("class", "x axis").call(ma_ax_x)
            ma_gp.append("g").attr("class", "y axis").call(ma_ax_y)

            // setup gradient, plot colorbar and its axes
            var cb_gd = cb_gp.append("defs").append("linearGradient").attr("id", "cbgrad")
                            .attr("x1", "0%").attr("x2", "0%").attr("y1", "0%").attr("y2", "100%")
            cb_gd.append("stop").attr("offset",   "0%").attr("style", "stop-color: rgb(255, 0,   0); stop-opacity:1")
            cb_gd.append("stop").attr("offset", "100%").attr("style", "stop-color: rgb(  0, 0, 255); stop-opacity:1")
            cb_gp.append("g").append("rect").attr("fill", "url(#cbgrad)")
                .attr("width", f.w()*f.pad()).attr("height", f.h()*(1 - 2*f.pad()))
            cb_gp.append("g").attr("transform", "translate("+ f.w()*f.pad() +", 0)").attr("class", "y axis").call(cb_ax_y)


            // add brush to colorbar
            f.br_colorbar = d3.svg.brush().y(cb_sc_y).on("brush", function() {
                var ext = f.br_colorbar.extent()
                ma_gp_rect_gp.selectAll("rect").classed("tv-colorbar-unselected", function(d) {
                    return ((d<ext[1]) && (d>ext[0])) ? false : true
                });
            })

            cb_gp.append("g").append("g").classed("brush", true).call(f.br_colorbar)
                .selectAll("rect").attr("width", f.w()*f.pad())

            // define premade update function, user could set their own
            f.update = function() {

                // inspect new data
                var mn = f.mat().min()
                  , mx = f.mat().max()

                // refresh the rect fills
                ma_gp_rect_gp.selectAll("rect").attr("fill", ma_gp_fill);

                // refresh the domain on colorbar
                cb_sc_y.domain([mx, mn])
                cb_gp.select(".y.axis").call(cb_ax_y)

                // refresh the color map
                ma_sc_c.domain([mn, mx])

            }
        }

        // generate configurators
        var conf_fields = ["w", "h", "pad", "mat", "mat_over"];
        conf_fields.map(function(name) { f[name] = tv.util.gen_access(f, name); })

        return f;
    },

    coh: function () {

        // translator helper
        function xl(x, y) { return "translate(" + x + ", " +  y + ")"; }

        function mean_axis_1_2(A) { // B = A.mean(axis=1).mean(axis=2)
            B = tv.ndar.zeros(A.shape[0])
            for (var i=0; i<A.shape[0]; i++) {
                for (var j=0; j<A.strides[1]; j++) {
                    B.data[i] += A.data[i*A.strides[0] + j]; } }
            return B.div(A.strides[1]);
        }

        function mean_axis_0(A, lo, hi) { // B = A[lo:hi].mean(axis=0)
            var nn  = A.shape[1]*A.shape[2]
              , res = tv.ndar.zeros(nn);
            for (var i=0; i<nn; i++) {
                for (var j=lo; j<hi; j++) {
                    res.data[i] += A.data[j*A.strides[0] + i]; } }
            res.idiv(nn);
            res.shape = [A.shape[1], A.shape[2]];
            res.strides = [A.shape[2], 1];
            return res;
        }

        var f = function (root) {

            // defaults
            f.w  (  f.w() || 800);
            f.h  (  f.h() || 400);
            f.pad(f.pad() || 0.1);

            // create svg of configured dimensions
            var svg = root//.append("svg").attr("width", f.w()).attr("height", f.h()) // TODO: clearup
              , llxf = xl(f.pad()*f.w(), f.h()*(1 - f.pad()));

            // get the data, compute average coherence spectrum
            var f_d = f.f(), coh_d = f.coh(), acoh_d = mean_axis_1_2(coh_d);

            // create scales and axes for frequency display
            var x_s = d3.scale.linear().domain([   f_d.min(),    f_d.max()]).range([0, f.w()/2 - 2*f.pad()*f.w() ]),
                y_s = d3.scale.linear().domain([acoh_d.min(), acoh_d.max()]).range([0, -(f.h()   - 2*f.pad()*f.h())]),
                x_a = d3.svg.axis().orient("bottom").scale(x_s),
                y_a = d3.svg.axis().orient(  "left").scale(y_s);
        
            // draw axes and average coherence
            svg.append("g").classed("axis", true).attr("transform", llxf).call(x_a);
            svg.append("g").classed("axis", true).attr("transform", llxf).call(y_a);
            svg.append("g").classed("line-plot", true)
                .attr("transform", xl(f.pad()*f.w(), f.h()*(1 - f.pad())))
                .selectAll("path").data([d3.zip(f_d.map(x_s).data, acoh_d.map(y_s).data)]).enter()
                .append("path")
                .attr("d", d3.svg.line())

            // setup matrix plot, initialized with all freq bands
            var selcoh_d = mean_axis_0(coh_d, 0, coh_d.shape[0])

            var mp_pl = tv.plot.mat().w(f.w()/2 - 1.5*f.pad()*f.w()).h( f.h()*(1 - 2*f.pad())).mat(selcoh_d).pad(0)
              , mp_gp = svg.append("g").attr("transform", "translate("+ f.w()/2 +", "+ f.pad()*f.h() +")")
              ;

            mp_pl(mp_gp);

            // add brush to select coherence data to show
            var brush    = d3.svg.brush().x(x_s).on("brush", function() {

                // find the extent and the selected index range
                var ex = brush.extent()
                  , lo = f_d.where(function(fi, i) { return ex[0] >= fi && ex[0] < f_d.data[i+1]; })[0]
                  , hi = f_d.where(function(fi, i) { return ex[1] >= fi && ex[1] < f_d.data[i+1]; })[0];

                // reset selected coherence data
                selcoh_d = brush.empty() ? mean_axis_0(coh_d, 0, coh_d.shape[0]) : mean_axis_0(coh_d, lo, hi);

                // update matrix plot
                mp_pl.mat(selcoh_d).update();

            });

            // add the brush to svg
            svg.append("g").attr("transform", xl(f.pad()*f.w(), f.h()*f.pad())).classed("brush", true)
                .call(brush).selectAll("rect").attr("height", f.h()*(1 - 2*f.pad()));

        }

        f.config_fields = ["f", "coh", "w", "h", "pad", "usage"];
        f.config_fields.forEach(function(name) {
            f[name] = tv.util.gen_access(f, name);
        });
        return f;
    },

    pca: function () { // my apologies! this needs rewriting.. 

        var f = function(root) {

            var u = f.u().mul(2*Math.PI)
              , n = u.length()
              , nkeep = f.nkeep() || 10
              , w = f.w() || 800
              , h = f.h() || 400
              , vt_raw = f.vt()
              , lines_space = 1.5

            // process slices
            slices = u.slice(0, nkeep).data;
            slices.push(u.slice(nkeep, u.length()).sum());
            slice_specs = [], slice_acc = 0;
            for (var i=0; i<slices.length; i++)
              { slice_specs[i] = {startAngle: slice_acc};
                slice_acc += slices[i];
                slice_specs[i].endAngle = slice_acc - 0.01; }

            // spread out colors for each component
            color_map = d3.scale.category10();

            // create different groups we'll use (not best strategy...)
            root.selectAll("g").data([{id:  "pie", x:   w/8, h:   h/2.2}, 
                                     {id: "bars", x: w/2, h:   h/2},
                                     {id: "text", x: 0.1*w, h: 0.95*h}])
                .enter().append("g").attr("id", function(d) { return d.id; })
                .attr("transform", function(d) { return "translate(" + d.x + ", " + d.h + ")"})

            // text displaying info on mouse over 
            root.select("g#text").append("text").classed("pca-text", true).text("");

            // create pie chart based on slices
            root.select("g#pie").selectAll("path").data(slice_specs).enter()
                .append("path")
                .style("fill", function (d, i) { return i === nkeep ? "#ddd" : color_map(i); })
                .attr("d", d3.svg.arc().innerRadius(50).outerRadius(150))
                .on("mouseover", function (d, i) { 
                    var u = f.u().data, txt;
                    if (i < nkeep) { var ord = tv.util.ord_nums[i+1], v = u[i]*100;
                                     txt = ord.slice(0, 1).toUpperCase() + ord.slice(1, ord.length) 
                                        + " component explains " + v.toPrecision(3) + " % of the variance."; }
                    else { var v = tv.ndar.from(u.slice(nkeep, u.length)).sum()*100;
                           txt =  "Other " + (n - nkeep) + " components explain " + v.toPrecision(3) + " % of the variance.";}
                    root.select("g#text").select("text").text(txt); 
                    vt_axes.select("path").style("stroke-width", function (e, j) { return i===j ? 3 : 1 ; }); })
                .on("mouseout", function (d, i) {
                        root.select("g#text").select("text").text("");
                        vt_axes.select("path").style("stroke-width", 1); });
            
            // group showing the singular vectors
            var vt = root.select("g#bars");

            // draw labels
            vt.append("g").selectAll("text").data(tv.ndar.range(n).data).enter()
                    .append("text").classed("node-labels", true)
                    .attr("transform", function (d) { return "translate(" + (w/lines_space/n)*(d-n/3) + ", " + -h/2.4 + ") rotate(-60) "; })
                    .text(function(d) { return "node " + d; }) // TODO use real node labels

            // draw vertical grid lines
            vt.append("g").attr("transform", "translate(" + -w/4.5 + "," + (-h/3-15) + ")").selectAll("line").data(tv.ndar.range(n).data).enter()
                .append("line").attr("x1", function (d) { return w/lines_space/n*d }).attr("x2", function (d) { return w/lines_space/n*d })
                .attr("y2", 2*h/3).attr("y1", -15).attr("stroke", function (d) { return d % 5 === 0 ? "#ccc" : "#eee"; });

            function vt_axes_yoff(d, i) { return i/nkeep*2*h/3 - h/3 }

            // organize the data (TODO: there's gotta be a better way of doing this)
            var vt_data = []
              , vt_scl = Math.max(-vt_raw.min(), vt_raw.max());

            for (var i=0; i<nkeep; i++) {
                vt_data[i] = [];
                for (var j=0; j<n; j++) {
                vt_data[i][j] = [j*w/lines_space/n, ( 2*h/3/nkeep/2 /vt_scl)*vt_raw.data[i*n + j]]; } }

            // setup axes groups, add zero lines, vector curves and plus/minus signs
            var vt_axes = vt.append("g").selectAll("g").data(vt_data).enter()
                    .append("g").attr("transform", function (d, i) { return "translate(" + -w/4.5 + ", " + vt_axes_yoff(d, i) + ")"; });

            vt_axes.append("line").attr("x2", w/lines_space).style("stroke", "black");
            vt_axes.append("path").attr("d", d3.svg.line()).attr("fill", "transparent").attr("stroke", function (d, i) { return color_map(i); });
            vt_axes.append("text").classed("vt-pm-sign", true).attr("x", -6).text("+")
            vt_axes.append("text").classed("vt-pm-sign", true).attr("x", -5).attr("y", 5).text("-")

        }

        var conf = ["w", "h", "pad", "nkeep", "u", "vt"]
        conf.map(function(name) { f[name] = tv.util.gen_access(f, name); }) 
        return f
    },

    time_series: function () {

        var f = function(root) {

            f.p(f.p() || 0.1) // pad
            f.w(f.w() || 700)
            f.h(f.h() || 500)
            f.point_limit(f.point_limit() || 500)

            f.magic_fcs_amp_scl = 1

            // make sure we got numbers not strings
            f.dt(+f.dt())
            f.t0(+f.t0())

			// Create the required UI elements.
            var div = root
              , svg = div.append("svg").attr("width", f.w()).attr("height", f.h())
              , rgp = svg.append("g").attr("transform", "scale(1, 1)")

            rgp.append("g").append("rect").attr("width", f.w()).attr("height", f.h()).classed("tv-fig-bg", true)

            f.status_line = svg.append("g").attr("transform", "translate(10, "+ (f.h() - 10) + ")")
                                .append("text")

            // parts independent of data
            f.compute_layout()
            f.add_resizer(svg, rgp)
            f.do_scaffolding(rgp)
            // f.add_notes(div) --- DEPRECATED by twotribes: No, no, no! We don't want to generate simple notes by JS!

            // inversion of flow control in progress
            f.we_are_setup = false
            f.render()

        } // end function f()

        f.render = function() {
            f.status_line.text("waiting for data from server...")
            tv.util.get_array_slice(f.baseURL(), f.current_slice(), f.render_callback, f.channels(), f.mode(), f.state_var())
        }

        f.render_callback = function(data) {

            var kwd = kwd || {};

            f.status_line.text("handling data...")

            /* reformat data into normal ndar style */
            var flat=[]
              , sl = f.current_slice()[0]
              , shape=[ (sl.hi - sl.lo)/sl.di, f.shape()[2]]
              , strides=[f.shape()[2], 1];

            for (var i=0; i<shape[0]; i++) {
                for (var j=0; j<shape[1]; j++) {
                    flat.push(data[i][j]);
                }
            }

            var ts = [], t0 = f.t0(), dt = f.dt();
            
            for (var i=0; i<shape[0]; i++) {
                ts.push(t0 + dt*sl.lo + i*dt*sl.di)
            }

            f.ts(tv.ndar.ndfrom({data: ts, shape:[shape[0]], strides: [1]}))
            f.ys(tv.ndar.ndfrom({data: flat, shape: shape, strides: strides}))

            f.status_line.text("examining data...")
            f.prepare_data()

            f.status_line.text("rendering data...")
            f.render_focus()

            if (!f.we_are_setup) {
                f.render_contexts()
                f.add_brushes()
                f.br_fcs_endfn(true) // no_render=true
                f.we_are_setup = true
            }

            f.status_line.text("")

        }

        f.current_slice = function () {
            var dom = f.sc_fcs_x.domain()
              , lo = Math.floor((dom[0] - f.t0())/f.dt())
              , hi = Math.floor((dom[1] - f.t0())/f.dt())
              , di = Math.floor((hi - lo)/f.point_limit())

            di = di===0 ? 1 : di

            if (lo>f.shape()[0]) {
                console.log("time_series.current_slice(): found lo>shape[0]: " + lo + ">" + f.shape()[0])
                lo = f.shape()[0]
            }

            return [{lo: lo, hi:hi, di: di}]
        }

        // dimensions and placement of focus and context areas
        f.compute_layout = function () {

            // pad is only provisionally basis for dimensioning the context areas; later
            // we will need to have inner and outer pad

            f.pad   =    {x:       (0 ? f.w() : f.h())*f.p(),  y:                 f.h()*f.p()}
            f.ul_ctx_y = {x:                         f.pad.x,  y:                     f.pad.y}
            f.sz_ctx_y = {x:                     f.pad.x*0.8,  y:  f.h()- 3*f.pad.y - f.pad.y}
            f.ul_ctx_x = {x:        2*f.pad.x + f.sz_ctx_y.x,  y:    2*f.pad.y + f.sz_ctx_y.y}
            f.sz_ctx_x = {x: f.w()- 3*f.pad.x - f.sz_ctx_y.x,  y:                     f.pad.y}
            f.ul_fcs   = {x:                    f.ul_ctx_x.x,  y:                f.ul_ctx_y.y}
            f.sz_fcs   = {x:                    f.sz_ctx_x.x,  y:                f.sz_ctx_y.y}

        }

        // allows user to scale plot size dynamically
        // TODO refactor place in tv.util
        f.add_resizer = function (svg, rgp) {

            var resize_start

            rgp.append("g").append("rect").classed("tv-resizer", true)
                .on("mouseover", function () { rgp.attr("style", "cursor: se-resize")})
                .on("mouseout", function () { rgp.attr("style", "")})
                .attr("x"    , f.w() - f.pad.x/2).attr("y"     , f.h() - f.pad.y/2)
                .attr("width",         f.pad.x/2).attr("height",         f.pad.y/2)
                .call(d3.behavior.drag().on("drag", function() {
                    var p1 = d3.mouse(svg.node())
                      , p2 = resizer_start
                      , scl = {x: p1[0]/p2[0], y: p1[1]/p2[1] }
                    rgp.attr("transform", "scale(" + scl.x + ", " + scl.y + ")")
                    svg.attr("width", scl.x*f.w()).attr("height", scl.y*f.h())
                }).on("dragstart", function() {
                    resizer_start = d3.mouse(rgp.node())
                }))
        }

        // TODO migrate to tv.util
        var new_clip_path = function (el, id) {
          return el.append("defs").append("clipPath").attr("id", id)
        }
        
        var add_canvas = function() {
          cv_ctx_x = gp_ctx_x.append("g").append("foreignObject")
                        .attr("width", sz_ctx_x.x).attr("height", sz_ctx_x.y).append("xhtml:canvas")
        }

        f.mouse_scroll = function(scroll_dim) {
            var ev = window.event
              , da = ev.detail ? ev.detail : ev.wheelDelta
              , sh = ev.shiftKey
              , dr = da > 0 ? true : false

            if (sh) {
                var scl = dr ? 1.2 : 1/1.2
                f.magic_fcs_amp_scl *= scl
                // TODO scale transform instead via direct access...
                f.prepare_data()
                f.render_focus()
            } else {
                var br = scroll_dim === "horizontal"
                if (!(f.br_ctx_y.empty())) {
                    var ext = f.br_ctx_y.extent()
                      , dx  = dr ? 1 : -1

                    f.br_ctx_y.extent([ext[0]+dx, ext[1]+dx])
                    f.br_ctx_y_fn()
                }
            }

        }

        f.signal_tick_labeler = function(tick_value) {
            return (tick_value%1===0) ? f.labels()[tick_value] : ""
        }

        // setup groups, scales and axes for context and focus areas
        f.do_scaffolding = function (rgp) {

            // main groups for vertical and horizontal context areas and focus area
            f.gp_ctx_y = rgp.append("g").attr("transform", "translate(" + f.ul_ctx_y.x + ", " + f.ul_ctx_y.y + ")")
            f.gp_ctx_x = rgp.append("g").attr("transform", "translate(" + f.ul_ctx_x.x + ", " + f.ul_ctx_x.y + ")")
            f.gp_fcs   = rgp.append("g").attr("transform", "translate(" + f.ul_fcs.x   + ", " + f.ul_fcs.y   + ")")
            f.gp_fcs.on("mousewheel", f.mouse_scroll)
            f.gp_fcs.append("rect").attr("width", f.sz_fcs.x).attr("height", f.sz_fcs.y).classed("tv-data-bg", true)
            f.gp_ctx_x.append("rect").attr("width", f.sz_ctx_x.x).attr("height", f.sz_ctx_x.y).classed("tv-data-bg", true)
            f.gp_ctx_y.append("rect").attr("width", f.sz_ctx_y.x).attr("height", f.sz_ctx_y.y).classed("tv-data-bg", true)

            // the plotted time series in the focus and x ctx area are subject to a clipping region
            new_clip_path(rgp, "fig-lines-clip").append("rect").attr("width", f.sz_fcs.x  ).attr("height", f.sz_fcs.y)
            new_clip_path(rgp, "fig-ctx-x-clip").append("rect").attr("width", f.sz_ctx_x.x).attr("height", f.sz_ctx_x.y)

            // group with clip path applied for the focus lines
            f.gp_lines = f.gp_fcs.append("g").attr("style", "clip-path: url(#fig-lines-clip)")
                                 .append("g").classed("line-plot", true)

            // scales for vertical and horizontal context, and the x and y axis of the focus area
            f.sc_ctx_y = d3.scale.linear().domain([    -1,                 f.shape()[2]  ]).range([f.sz_ctx_y.y,            0])
            f.sc_ctx_x = d3.scale.linear().domain([f.t0(),   f.t0()+f.dt()*f.shape()[0]  ]).range([           0, f.sz_ctx_x.x])
            f.sc_fcs_x = d3.scale.linear().domain([f.t0(),   f.t0()+f.dt()*f.shape()[0]  ]).range([           0, f.sz_fcs.x  ])
            f.sc_fcs_y = d3.scale.linear().domain([    -1,                 f.shape()[2]+1]).range([f.sz_fcs.y  ,            0])

            // axes for each of the above scales
            f.ax_ctx_y = d3.svg.axis().orient(  "left").scale(f.sc_ctx_y)
            f.ax_ctx_x = d3.svg.axis().orient("bottom").scale(f.sc_ctx_x)
            f.ax_fcs_x = d3.svg.axis().orient(   "top").scale(f.sc_fcs_x)
            f.ax_fcs_y = d3.svg.axis().orient(  "left").scale(f.sc_fcs_y)

            f.ax_fcs_y.tickFormat(f.signal_tick_labeler)
            f.ax_ctx_y.tickFormat(f.signal_tick_labeler)

            // groups for each of the above axes
            f.gp_ax_ctx_y = f.gp_ctx_y.append("g").classed("axis", true).call(f.ax_ctx_y)
            f.gp_ax_ctx_x = f.gp_ctx_x.append("g").classed("axis", true).call(f.ax_ctx_x)
                                        .attr("transform", "translate(0, " + f.sz_ctx_x.y + ")")
            f.gp_ax_fcs_x = f.gp_fcs  .append("g").classed("axis", true).call(f.ax_fcs_x)
            f.gp_ax_fcs_y = f.gp_fcs  .append("g").classed("axis", true).call(f.ax_fcs_y)

        } 

        f.prepare_data = function() {


            //, get_array_slice: function(gid, slices, callback) {

            var ts = f.ts()
              , ys = f.ys()


            /*
                To set this properly, we need to know
                    
                    nsig - how many signals on the screen?
                    std  - std of signals
                    pxav - vertical pixels available

            */

            var da_lines = [], line_avg;

            for (var sig_idx=0; sig_idx<ys.shape[1]; sig_idx++) {
            
                da_lines[sig_idx] = []
                for (var t_idx=0; t_idx<ys.shape[0]; t_idx++) {
                    da_lines[sig_idx][t_idx] = ys.data[ys.strides[0]*t_idx + sig_idx]
                }

                line_avg = d3.mean(da_lines[sig_idx])

                for (var t_idx=0; t_idx<ys.shape[0]; t_idx++) {
                    da_lines[sig_idx][t_idx] = f.magic_fcs_amp_scl*(da_lines[sig_idx][t_idx] - line_avg)
                }

                da_lines[sig_idx] = {sig: da_lines[sig_idx],
                                     id : sig_idx}
            }

            // take me out to eat indian, I can't get enough of this NaN!

            // compute context data
            var da_x = []
              , da_xs= []
              , da_y = []
              , ys_mean = ys.mean()
              , ys_std  = ys.std()
              , n_chan  = ys.shape[1]
              , ts_max = ts.max()
              , datum

            // center and scale to std an average signal     
            for (var j=0; j<ts.shape[0]; j++) {
                da_x[j]  = 0
                da_xs[j] = 0
                for (var i=0; i<n_chan; i++) {
                    datum = ys.data[ j*n_chan + i ]
                    da_x [j] += datum
                    da_xs[j] += datum*datum
                }
                da_xs[j] = Math.sqrt(da_xs[j]/n_chan - ((da_x[j]/n_chan)*(da_x[j]/n_chan)))
                da_x [j] = (da_x[j]/n_chan - ys_mean)/ys_std

                if ((da_x[j] === NaN) || (da_xs[j] === NaN)) {
                    console.log("encountered NaN in data: da_x[" + j + "] = " + da_x[j] + ", da_xs[" + j + "] = " + da_xs[j] + ".");
                }
            }

            // center and scale the std line
            da_xs.min = tv.ndar.from(da_xs).min()

            for (var j=0; j<da_xs.length; j++) {
                da_xs[j] -= da_xs.min
                da_xs[j] /= ys_std
            }

            // center and scale to std each signal
            for (var j=0; j<n_chan; j++) {
                da_y[j] = []
                for (var i=0; i<f.sz_ctx_y.x; i++)
                    da_y[j][i] = (ys.data[ i*n_chan + j ] - ys_mean)/ys_std
            }

            f.da_lines = da_lines
            f.da_x_dt = f.dt()*f.current_slice()[0].di
            f.da_x = da_x
            f.da_xs= [0, da_xs[da_xs.length-1]].concat(da_xs, [0]) // filled area needs start == end
            f.da_y = da_y

        }

        f.render_focus = function () {

            var ts = f.ts()
              , g  = f.gp_lines.selectAll("g").data(f.da_lines, function(d) {return d.id})

            if (!f.we_are_setup) {
                f.line_paths = g.enter()
                    .append("g")
                        .attr("transform", function(d, i) { return "translate(0, " + f.sc_fcs_y(i) + ")"})
                    .append("path")
            }

            g.select("path").attr("d", function(d, j) {
                return d3.svg.line().x(function(dd, i) { return f.sc_ctx_x(ts.data[i]) })
                                    .y(function(dd   ) { return dd })
                                    (d.sig)
            })
        }

        f.render_contexts = function () {

            var ts = f.ts()

            // horizontal context line
            f1 = f.gp_ctx_x.append("g").attr("style", "clip-path: url(#fig-ctx-x-clip)")
            f2 = f1.selectAll("g").data([f.da_x]).enter()
            f3 = f2.append("g").attr("transform", function(d, i) { return "translate(0, " + (f.sz_ctx_x.y/2) + ") scale(1, 0.5)" })
                            .classed("tv-ctx-line", true)
            f4 = f3.append("path")
                    .attr("d", d3.svg.line().x(function (d, i) { return f.sc_ctx_x( (ts.data[0] + i)*f.da_x_dt) })
                                            .y(function (d, i) { return d*f.sz_ctx_x.y }))

            // error on context line
            // TODO the data for this path needs to be re done so that it traces above and below
            // the mean line. 
            var da_x_len = f.da_x.length

            f.gp_ctx_x.append("g").attr("style", "clip-path: url(#fig-ctx-x-clip)")
                .selectAll("g").data([f.da_x.concat(f.da_x.slice().reverse())])
              .enter()
                .append("g").attr("transform", "translate(0, " + f.sz_ctx_x.y/2 + ") scale(1, 0.5)")
                            .classed("tv-ctx-error", true)
                .append("path")
                    .attr("d", d3.svg.line().x(function(d, i) {
                        var idx = (i<da_x_len) ? i : (2*da_x_len - i)
                        return f.sc_ctx_x(idx*f.da_x_dt) 
                    }).y(function(d, i) { 
                        var std = (i<da_x_len) ? f.da_xs[i] : -f.da_xs[2*da_x_len - i - 1]
                        return f.sz_ctx_x.y*(d + std)
                    }))

            // vertical context lines
            f.gp_ctx_y.append("g").selectAll("g").data(f.da_y)
              .enter()
                .append("g").attr("transform", function(d, i) { return "translate(0, " + f.sc_ctx_y(i) + ")" })
                            .classed("tv-ctx-line", true)
                .append("path")
                    .attr("d", d3.svg.line().x(function(d, i) { return 2+(f.sz_ctx_y.x - 2)*i/f.sz_ctx_y.x })
                                            .y(function(d, i) { return d }))
        }

        f.scale_focus_stroke = function () {
            var total = f.sz_fcs
              , xdom  = f.sc_fcs_x.domain()
              , ydom  = f.sc_fcs_y.domain()
              , dx    = f.sc_fcs_x(xdom[1]) - f.sc_fcs_x(xdom[0])
              , dy    = f.sc_fcs_y(ydom[1]) - f.sc_fcs_y(ydom[0])
              , area  = dx*dy
              , area2 = total.x*total.y

            console.log(area/area2)
            f.gp_lines.attr("style", "stroke-width: " + Math.abs(area/area2))
        }

        f.add_brushes = function () {

            // horizontal context brush
            var br_ctx_x_fn = function () {
                var dom = f.br_ctx_x.empty() ? f.sc_ctx_x.domain() : f.br_ctx_x.extent()
                  , sc = f.sc_fcs_x
                  , x_scaling = f.sc_ctx_x.domain()[1]/(dom[1] - dom[0]);
                
                sc.domain(dom)
                f.gp_ax_fcs_x.call(f.ax_fcs_x)
                // TODO: This seems to cause problems with negative values and comenting it out does not seem to
                // cause any additional problems. This could do with some double checking.
                // f.gp_lines.attr("transform", "translate(" + sc(0) + ", 0) scale(" + x_scaling + ", 1)")
				
            }

            // vertical context brush
              , br_ctx_y_fn = function () {
                var dom = f.br_ctx_y.empty() ? f.sc_ctx_y.domain() : f.br_ctx_y.extent()
                  , yscl = f.sz_fcs.y / (dom[1] - dom[0]) / 30
                f.sc_fcs_y.domain(dom)
                f.gp_ax_fcs_y.call(f.ax_fcs_y)
                f.gp_lines.selectAll("g").attr("transform", function(d, i) { 
                    return "translate(0, " + f.sc_fcs_y(i) + ") scale (1, " + yscl +")" 
                })
            }

              , br_ctx_end = function () {
                f.scale_focus_stroke()
                // TODO: This f.render() only makes another call to the server bringing back data that is already here.
                // Also when rerendering that data it is rendered from the 0 timeline, so if for example you
                // zoom on a block from 250-270, 20 points or data ar brought from the server and the plot is
                // redrawn with data from 0-20, but you being in the area 250-270 don't see any of it. This needs
  				// to be tested further to see if it was really needed, and if so look into the problem of zooming
  				// described above.
  				
                // f.render()
            }

            f.br_ctx_y_fn = br_ctx_y_fn;

            // on end of focus brush
            // this is on f so that f can call it when everything else is done..
            f.br_fcs_endfn = function(no_render) {

                br_ctx_x_fn()
                br_ctx_y_fn()
                f.scale_focus_stroke()
                f.gp_br_fcs.call(f.br_fcs.clear())

                if (!no_render) {
                	// TODO: This f.render() only makes another call to the server bringing back data that is already here.
	                // Also when rerendering that data it is rendered from the 0 timeline, so if for example you
	                // zoom on a block from 250-270, 20 points or data ar brought from the server and the plot is
	                // redrawn with data from 0-20, but you being in the area 250-270 don't see any of it. This needs
	  				// to be tested further to see if it was really needed, and if so look into the problem of zooming
	  				// described above.
  				
                    // f.render()
                }
            }

            // focus brush
            , br_fcs_brush = function() {
                var ex = f.br_fcs.extent()
                f.br_ctx_x.extent([ex[0][0], ex[1][0]])
                f.br_ctx_y.extent([ex[0][1], ex[1][1]])
                f.gp_br_ctx_y.call(f.br_ctx_y)
                f.gp_br_ctx_x.call(f.br_ctx_x)
            }

            // create brushes
            f.br_ctx_x = d3.svg.brush().x(f.sc_ctx_x).on("brush", br_ctx_x_fn)
                                                     .on("brushend", br_ctx_end)

            f.br_ctx_y = d3.svg.brush().y(f.sc_ctx_y).on("brush", br_ctx_y_fn)
                                                     .on("brushend", br_ctx_end)

            f.br_fcs   = d3.svg.brush().x(f.sc_fcs_x)
                                       .y(f.sc_fcs_y).on("brushend", f.br_fcs_endfn)
                                                     .on("brush"   ,   br_fcs_brush)

            // add brush groups and add brushes to them
            f.gp_br_ctx_y = f.gp_ctx_y.append("g")
            f.gp_br_ctx_x = f.gp_ctx_x.append("g")
            f.gp_br_fcs   = f.gp_fcs  .append("g").classed("brush", true).call(f.br_fcs)

            f.gp_br_ctx_y.append("g").classed("brush", true).call(f.br_ctx_y).selectAll("rect").attr("width" , f.sz_ctx_y.x)
            f.gp_br_ctx_x.append("g").classed("brush", true).call(f.br_ctx_x).selectAll("rect").attr("height", f.sz_ctx_x.y)
        }

		// THIS FUNCTION IS ALREADY DEPRECATED by twotribes as of 0.9.10
        f.add_notes = function (div) {

            tv.util.usage(div, "", ["Click and drag the blue box in the lower right to resize the viewer"])

            tv.util.usage(div, "focus (center area)", 
                    ["Click and drag to zoom",
                    "Click once to reset zoom",
                    "Mouse/scroll wheel to navigate to scroll signals",
                    "Shift + Mouse/scroll wheel to scale signal amplitudes",
                    ])

            tv.util.usage(div, "temporal context (horizontal, bottom)",
                    ["Solid line marks mean across channels, in time",
                    "Shaded area marks standard deviation across channels, in time",
                    "Click and drag to select a subset of signals",
                    "Click and drag a selection to change selected signals",
                    "Click outside selection box to cancel and reset view"])

            tv.util.usage(div, "signal context (vertical, left)",
                    ["Solid lines show each signal",
                    "Click and drag to select a subset of signals",
                    "Click and drag a selection to change selected signals",
                    "Click outside selection box to cancel and reset view"])
        }

        f.proof_of_concept_canvas_in_svg = function () {
            var ctx = cv_ctx_x.node().getContext("2d");
            ctx.fillStyle = "#000"
            ctx.fillRect(0, 0, 10, 10)
        }

        f.parameters = ["w", "h", "p","baseURL", "preview", "labels", "shape", "t0", "dt", "ts", "ys", "point_limit", "channels", "mode", "state_var"]
        f.parameters.map(function(name) { f[name] = tv.util.gen_access(f, name) })

        return f

    },

    components: function () {

        var f = function(root) {

            var cs = f.components()
              , n = cs.shape[0]
              , w = f.w() || 800
              , h = f.h() || 400

            // group showing the singular vectors
            var vt = root.append("g")

            // draw labels
            vt.append("g").selectAll("text").data(tv.ndar.range(n).data).enter()
                    .append("text").classed("node-labels", true)
                    .attr("transform", function (d) { return "translate(" + (w/2.25/n)*(d-n/2) + ", " + -h/2.4 + ") rotate(-60) "; })
                    .text(function(d) { return "node " + d; }) // TODO use real node labels

            // draw vertical grid lines
            vt.append("g").attr("transform", "translate(" + -w/4.5 + "," + (-h/3-15) + ")").selectAll("line").data(tv.ndar.range(n).data).enter()
                .append("line").attr("x1", function (d) { return w/2.25/n*d }).attr("x2", function (d) { return w/2.25/n*d })
                .attr("y2", 2*h/3).attr("y1", -15).attr("stroke", function (d) { return d % 5 === 0 ? "#ccc" : "#eee"; });

            function vt_axes_yoff(d, i) { return i/nkeep*2*h/3 - h/3 }

            // organize the data (TODO: there's gotta be a better way of doing this)
            var vt_data = []
              , vt_scl = Math.max(-cs.min(), cs.max());

            for (var i=0; i<nkeep; i++) {
                vt_data[i] = [];
                for (var j=0; j<n; j++) {
                vt_data[i][j] = [j*w/2.25/n, ( 2*h/3/nkeep/2 /vt_scl)*cs.data[i*n + j]]; } }

            // setup axes groups, add zero lines, vector curves and plus/minus signs
            var vt_axes = vt.append("g").selectAll("g").data(vt_data).enter()
                    .append("g").attr("transform", function (d, i) { return "translate(" + -w/4.5 + ", " + vt_axes_yoff(d, i) + ")"; });

            vt_axes.append("line").attr("x2", w/2.25).style("stroke", "black");
            vt_axes.append("path").attr("d", d3.svg.line()).attr("fill", "transparent").attr("stroke", function (d, i) { return color_map(i); });
            vt_axes.append("text").classed("vt-pm-sign", true).attr("x", -6).text("+")
            vt_axes.append("text").classed("vt-pm-sign", true).attr("x", -5).attr("y", 5).text("-")

        }

        var conf = ["w", "h", "pad", "components"]
        conf.map(function(name) { f[name] = tv.util.gen_access(f, name); }) 
        return f
    },

    ica: function () {

        var f = function(root) {

            var w = f.w() || 800
              , h = f.h() || 500
              ;

            root.append("g").attr("transform", "translate(" + w/4 + ", " + h/2 + ")")
                .append("text").attr("style", "font-size: 20")
                    .text("not implemented yet!");

        };

        var conf = ["w", "h", "pad", "components", "ts", "ys"]
        conf.map(function(name) { f[name] = tv.util.gen_access(f, name); }) 
        return f
    }

}


