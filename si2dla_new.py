from fst_object import *
from ostia_d import *
from helper import *


# Helper functions

def suff_1(w):
    """Returns 1-suffix of w"""
    if w == "":
        return ""
    else:
        return w[-1]


def get_OS(T,q):
    """Gets output 1-suffixes of state q in FST T"""
    incoming = { tr for tr in T.E if tr[3] == q}
    outs = { tr[2] for tr in incoming}
    suffs = { suff_1(w) for w in outs}
    return suffs


def lncat(w,v):
    """Returns wv^-1; i.e. v removed from the end of w"""
    if v == "":
        return w
    elif w.endswith(v):
        return w[0:-len(v)]
    else: 
        print ("using fake lncat")
        return w
        


def si2dla_ex(Dom,D,Rho,Sigma):
    """A less strict version of SI2LDA for dealing with a wider range of data sets"""

    print("Learning from "+str(D)+"\n")

    T_f = ostia_d(Dom,D,Rho,Sigma)

    print("Initial hypothesis for T_f:")
    print("  Q:\t"+str(T_f.Q))
    print("  E:\t"+str(T_f.E))
    print("  q0:\t"+str(T_f.qe))
    print("  stout:\t"+str(T_f.stout)+"\n")

    q1 = T_f.Q[0]
    q2 = T_f.Q[1]
    
    # error check in here
    OS = { q1 : get_OS(T_f,q1) | {""},
           q2 : get_OS(T_f,q2)
    }

    print("OSs for T_f:\t"+str(OS))

    #*** construct_T_g

    Q_g = ["qe","qd"]

    corr = {}
    rroc = {}

    if len(OS[q1]) < len(OS[q2]):
        corr["qe"] = q1
        corr["qd"] = q2
        rroc[q1] = "qe"
        rroc[q2] = "qd"
    else:
        corr["qe"] = q2
        corr["qd"] = q1
        rroc[q2] = "qe"
        rroc[q1] = "qd"

    print("corr:\t\t"+str(corr))
    # print("rroc:\t\t"+str(rroc))

    IS = { "qe" : OS[corr["qe"]],
           "qd" : OS[corr["qd"]]
    }

    if len(IS["qe"]) > 1:
        IS["qe"] = IS["qe"] - (IS["qe"] & IS["qd"])
    IS["qd"] = IS["qd"] - (IS["qe"] & IS["qd"])

    print("ISs for T_g:\t"+str(IS)+"\n")

    d_g = {}

    for q in Q_g:
        for s in Sigma:
            if s in IS["qe"]:
                d_g[(q,s)] = "qe"
            else:
                d_g[(q,s)] = "qd"
            # for r in Q_g:
            #     if s in IS[r]:
            #         d_g[(q,s)] = r

    # print("d_g:\t"+str(d_g))

    o_g = {}

    for s in Sigma:
        o_g[("qd",s)] = s

        # New here: look for *each* transition whose output starts with s, and see if there is a matching
        # transition from corr[qe]. This allows us to calculate s with a single transition from corr[qe],
        # instead of necessarily needing *every* transition from corr[qd] paired with one from corr[qe].
        d_trs = [ tr for tr in T_f.E if tr[0] == corr["qd"] and tr[2][0] == s ]

        found = False

        for t in d_trs:
            w_trs = [ tr for tr in T_f.E if tr[0] == corr["qe"] and tr[1] == t[1]]

            if w_trs != []:

                found = True

                w_d = t[2]

                w_e = w_trs[0][2]

                print("w_d for "+s+":\t"+w_d)
                print("w_e for "+s+":\t"+w_e+"\n")

                w_s = lncat(w_e,w_d[1:])

                o_g[("qe",s)] = w_s

                if s != w_s: #This is lns 2-3 from Alg 3
                    tau = s
                    w_tau = w_s

        if found == False:
            o_g[("qe",s)] = s


    # Translate transitions into fst_object FST format
    E_g = []

    for (q,s) in d_g.keys():
        E_g.append((q,s,o_g[(q,s)],d_g[(q,s)]))

    # print("E_g:\t"+str(E_g))

    T_g = FST(Rho,Sigma)
    T_g.Q = Q_g
    T_g.E = E_g
    T_g.qe = rroc[q1]
    T_g.stout = { "qe" : T_f.stout[corr["qe"]], "qd" : T_f.stout[corr["qd"]] }

    print("Hypothesis for T_g:")
    print("  Q:\t"+str(T_g.Q))
    print("  E:\t"+str(T_g.E))
    print("  q0:\t"+str(T_g.qe))
    print("  stout:\t"+str(T_g.stout)+"\n")


    #*** modify_T_f

    T_f.E = [ d for d in T_f.E if not d[0]==corr["qe"]]

    print("E_f after deletions: "+str(T_f.E)+"\n")

    new_E = []

    for (q,rho,w,r) in T_f.E:
        if q == corr["qd"]:
            if suff_1(w) not in IS[rroc[r]]:
                w = lncat(w,w_tau)+tau
        new_E.append((q,rho,w,q)) #Step 1 of merging is here too

    T_f.E = new_E

    print("E_f after opacity adjustment: "+str(T_f.E)+"\n")

    print("Merging...\n")

    T_f.Q = [corr["qd"]]
    T_f.qe = corr["qd"]
    T_f.stout = {corr["qd"]:T_f.stout[corr["qe"]]}

    print("Final hypothesis for T_f:")
    print("  Q:\t"+str(T_f.Q))
    print("  E:\t"+str(T_f.E))
    print("  q0:\t"+str(T_f.qe))
    print("  stout:\t"+str(T_f.stout)+"\n")

    return (T_f,T_g)
