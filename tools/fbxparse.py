import struct, zlib, sys
def read_fbx(path):
    d=open(path,'rb').read()
    ver=struct.unpack('<I',d[23:27])[0]
    wide=ver>=7500
    def rprop(p):
        t=chr(d[p]);p+=1
        if t in 'YCIFDL':
            fmt={'Y':'<h','C':'<?','I':'<i','F':'<f','D':'<d','L':'<q'}[t]
            v=struct.unpack_from(fmt,d,p)[0];return v,p+struct.calcsize(fmt)
        if t in 'SR':
            n=struct.unpack_from('<I',d,p)[0];p+=4;v=d[p:p+n];p+=n
            return (v.decode('utf8','replace') if t=='S' else v),p
        if t in 'fdlib':
            n,enc,cl=struct.unpack_from('<III',d,p);p+=12;raw=d[p:p+cl];p+=cl
            if enc==1: raw=zlib.decompress(raw)
            fmt={'f':'f','d':'d','l':'q','i':'i','b':'?'}[t]
            return list(struct.unpack('<%d%s'%(n,fmt),raw)),p
        raise ValueError(t)
    def rnode(p):
        if wide: end,np_,pl=struct.unpack_from('<QQQ',d,p);p+=24
        else: end,np_,pl=struct.unpack_from('<III',d,p);p+=12
        nl=d[p];p+=1
        if end==0: return None,p
        name=d[p:p+nl].decode();p+=nl
        props=[]
        for _ in range(np_):
            v,p=rprop(p);props.append(v)
        kids=[]
        while p<end:
            k,p=rnode(p)
            if k is None: break
            kids.append(k)
        return (name,props,kids),end
    p=27;nodes=[]
    while p<len(d)-200:
        n,p=rnode(p)
        if n is None: break
        nodes.append(n)
    return nodes
def find(n,name): return [k for k in n[2] if k[0]==name]
