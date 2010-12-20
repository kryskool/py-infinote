'''
Copyright (c) 2009 Simon Veith <simon@jinfinote.com>
Python port of Simon Veith's jinfinote implementation, written for the HWIOS project

Copyright (c) Contributors, http://hwios.org/
See CONTRIBUTORS for a full list of copyright holders.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.
    * Neither the name of the HWIOS Project nor the
    names of its contributors may be used to endorse or promote products
    derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE DEVELOPERS ``AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''
import sys
import re

class Operations(object):
    pass


class NoOp(Operations):
    '''Instantiates a new NoOp operation object.
    @class An operation that does nothing.
    '''
    requiresCID = False
    
    
    def toString(self):
        return "NoOp()"
        
    def toHTML(self):
        return "NoOp()"
        
    
    def apply(self, buffer):
        '''Applies this NoOp operation to a buffer. This does nothing, per definition. */'''
        pass 
    

    def transform(self, other):
        '''Transforms this NoOp operation against another operation. This returns a
        new NoOp operation.
        @type Operations.NoOp
        '''    
        return NoOp()
        
    
    def mirror(self):
        '''Mirrors this NoOp operation. This returns a new NoOp operation.
        @type Operations.NoOp
        '''
        return NoOp()
        

class Insert(Operations):
    '''Instantiates a new Insert operation object.
    @class An operation that inserts a Buffer at a certain offset.
    @param {Number} position The offset at which the text is to be inserted.
    @param {Buffer} text The Buffer to insert.
    '''
    requiresCID = True
    
    def __init__(self, position, text):
        self.position = position
        self.text = text
        

    def toString(self):
        return "Insert(%s, %s)" % (self.position, self.text)
        

    def toHTML(self):
        return "Insert(%s, %s)" % (self.position, self.text.toHTML())
        

    def apply(self, buffer):
        '''Applies the insert operation to the given Buffer.
        @param {Buffer} buffer The buffer in which the insert operation is to be performed.
        '''
        buffer.splice(self.position, 0, self.text)
        
    
    def cid(self, other):
        '''Computes the concurrency ID against another Insert operation.
        @param {Operations.Insert} other
        @returns The operation that is to be transformed.
        @type Operations.Insert
        '''
        if(self.position < other.position):
            return other
        if(self.position > other.position):
            return self
            

    def getLength(self):
        '''Returns the total length of data to be inserted by this insert operation,
        in characters.
        @type Number
        '''
        return self.text.getLength()
        
        
    def transform(self, other, cid):
        '''Transforms this Insert operation against another operation, returning the
        resulting operation as a new object.
        @param {Operation} other The operation to transform against.
        @param {Operation} [cid] The cid to take into account in the case of
        conflicts.
        @type Operation
        '''
        if isinstance(other, NoOp):
            return Insert(self.position, self.text)
        if isinstance(other, Split):
            #We transform against the first component of the split operation first.
            if cid == self:
                transformFirst = self.transform(other.first, self)
            else:
                transformFirst = self.transform(other.first, other.first)
            #The second part of the split operation is transformed against its first part.
            newSecond = other.second.transform(other.first)   
            if cid == self:                
                transformSecond = transformFirst.transform(newSecond, transformFirst)
            else:
                transformSecond = transformFirst.transform(newSecond, newSecond)   
            return transformSecond            
           
        pos1 = self.position
        str1 = self.text
        pos2 = self.position
    
        if isinstance(other, Insert):            
            str2 = other.text        
            if(pos1 < pos2 or (pos1 == pos2 and cid == other)):
                return Insert(pos1, str1)
            if(pos1 > pos2 or (pos1 == pos2 and cid == self)):
                return Insert(pos1 + str2.getLength(), str1)
        elif isinstance(other, Delete): 
            len2 = other.getLength()
        
            if(pos1 >= pos2 + len2):
                return Insert(pos1 - len2, str1)
            if(pos1 < pos2):
                return Insert(pos1, str1)
            if(pos1 >= pos2 and pos1 < pos2 + len2):
                return Insert(pos2, str1)
                

    def mirror(self):        
        '''Returns the inversion of this Insert operation.
        @type Operations.Delete
        '''
        return Delete(self.position, self.text.copy())


class Delete(Operations):
    '''Instantiates a new Delete operation object.
    Delete operations can be reversible or not, depending on how they are
    constructed. Delete operations constructed with a Buffer object know which
    text they are removing from the buffer and can therefore be mirrored,
    whereas Delete operations knowing only the amount of characters to be
    removed are non-reversible.
    @class An operation that removes a range of characters in the target
    buffer.
    @param {Number} position The offset of the first character to remove.
    @param what The data to be removed. This can be either a numeric value
    or a Buffer object.
    '''
    requiresCID = False
    
    def __init__(self, position, what, recon = None):
        self.position = position
        
        if isinstance(what, Buffer):
            self.what = what.copy()
        else:
            self.what = what
        if recon != None:
            self.recon = recon
        else:
            self.recon = Recon()
            
    
    def toString(self):
        return 'Delete(%s, %s)' % (self.position, self.what)
        

    def toHTML(self):
        if isinstance(self.what, Buffer):
            return 'Delete(%s, %s)' % (self.position, self.what.toHTML())
        else:
            return 'Delete(%s, %s)' % (self.position, self.what)
        

    def isReversible(self): 
        '''Determines whether this Delete operation is reversible.
        @type Boolean
        '''
        return isinstance(self.what, Buffer)
        
    
    def apply(self, buffer):
        '''Applies this Delete operation to a buffer.
        @param {Buffer} buffer The buffer to which the operation is to be applied.
        '''
        buffer.splice(self.position, self.getLength())


    def cid(self, other):
        pass
    

    def getLength(self):
        '''Returns the number of characters that this Delete operation removes.
        @type Number
        '''
        if(self.isReversible()):
            return self.what.getLength()
        else:
            return self.what
            

    def split(self, at):        
        '''Splits this Delete operation into two Delete operations at the given
        offset. The resulting Split operation will consist of two Delete
        operations which, when combined, affect the same range of text as the
        original Delete operation.
        @param {Number} at Offset at which to split the Delete operation.
        @type Operations.Split
        '''
        if self.isReversible():
            #This is a reversible Delete operation. No need to to any processing for recon data.
            return Split(
                Delete(self.position, self.what.slice(0, at)),
                Delete(this.position + at, self.what.slice(at))
            )
        else:
            '''This is a non-reversible Delete operation that might carry recon
            data. We need to split that data accordingly between the two new components.
            '''
            recon1 = Recon()
            recon2 = Recon()
        
            for index in self.recon.segments:
                if(self.recon.segments[index].offset < at):
                    recon1.segments.push(self.recon.segments[index])
                else:
                    recon2.segments.push(ReconSegment(self.recon.segments[index].offset - at, self.recon.segments[index].buffer))        
        return Split(Delete(self.position, at, recon1), Delete(self.position + at, self.what - at, recon2))


    def getAffectedString(self, operation, buffer):
        '''Returns the range of text in a buffer that this Delete or Split-Delete operation removes.
        @param operation A Split-Delete or Delete operation
        @param {Buffer} buffer
        @type Buffer
        '''
        if isinstance(operation, Split):           
            #The other operation is a Split operation. We call this function again recursively for each component.
            part1 = Delete.getAffectedString(operation.first, buffer)
            part2 = Operations.Delete.getAffectedString(operation.second, buffer)
            part2.splice(0, 0, part1)
            return part2
        elif isinstance(operation,Delete):
            '''In the process of determining the affected string, we also
            have to take into account the data that has been "transformed away"
            from the Delete operation and which is stored in the Recon object.
            '''        
            reconBuffer = buffer.slice(operation.position, operation.position + operation.getLength())
            operation.recon.restore(reconBuffer)
            return reconBuffer


    def makeReversible(self, transformed, state):
        '''Makes this Delete operation reversible, given a transformed version of 
        this operation in a buffer matching its state. If this Delete operation is
        already reversible, this function simply returns a copy of it.
        @param {Operations.Delete} transformed A transformed version of this operation.
        @param {State} state The state in which the transformed operation could be applied.
        '''
        if isinstance(self.what, Buffer):
            return Delete(self.position, self.what)
        else:
            return Delete(self.position, Delete.getAffectedString(transformed, state.buffer))


    def merge(self, other):
        '''Merges a Delete operation with another one. The resulting Delete operation
        removes the same range of text as the two separate Delete operations would
        when executed sequentially.
        @param {Operations.Delete} other
        @type Operations.Delete
        '''
        if self.isReversible():
            if not other.isReversible():
                raise 'Cannot merge reversible operations with non-reversible ones'
            newBuffer = self.what.copy()            
            newBuffer.splice(newBuffer.getLength(), 0, other.what)
            return Delete(self.position, newBuffer)
        else:
            newLength = self.getLength() + other.getLength()
            return Delete(self.position, newLength)


    def transform(self, other, cid):       
        '''Transforms this Delete operation against another operation.
        @param {Operation} other
        @param {Operation} [cid]
        '''
        if isinstance(other, NoOp):
            return Delete(self.position, self.what, self.recon)    
        if isinstance(other, Split):
            #We transform against the first component of the split operation first.
            if cid == self:
                transformFirst = self.transform(other.first, self)
            else:
                transformFirst = self.transform(other.first, other.first)        
            #The second part of the split operation is transformed against its first part.
            newSecond = other.second.transform(other.first) 
            if cid == this:
                transformSecond = transformFirst.transform(newSecond,transformFirst)
            else:
                transformSecond = transformFirst.transform(newSecond,newSecond)
            return transformSecond
    
        pos1 = self.position
        len1 = self.getLength()
    
        pos2 = other.position
        len2 = other.getLength()
    
        if isinstance(other,Insert):
            if (pos2 >= pos1 + len1):
                return Delete(pos1, self.what, self.recon)
            if(pos2 <= pos1):
                return Delete(pos1 + len2, self.what, self.recon)
            if pos2 > pos1 and pos2 < (pos1 + len1):
                result = self.split(pos2 - pos1)
                result.second.position += len2
                return result
            
    
        elif isinstance(other,Delete): 
            if (pos1 + len1) <= pos2:
                return Delete(pos1, self.what, self.recon)
            if (pos1 >= pos2) + len2:
                return Delete(pos1 - len2, self.what, self.recon)
            if (pos2 <= pos1) and (pos2 + len2) >= (pos1 + len1):
                '''     1XXXXX|
                2-------------|
                
                This operation falls completely within the range of another,
                i.e. all data has already been removed. The resulting
                operation removes nothing.
                '''
                if self.isReversible():
                    newData = Buffer()
                else:
                    newData = 0
                newRecon = self.recon.update(0,other.what.slice(pos1 - pos2, pos1 - pos2 + len1) )
                return Delete(pos2, newData, newRecon)
            if (pos2 <= pos1 and pos2 + len2 < pos1 + len1):
                '''   1XXXX----|
                2--------|                 
                The first part of this operation falls within the range of another.
                '''
                result = self.split(pos2 + len2 - pos1)
                result.second.position = pos2
                result.second.recon = self.recon.update(0,other.what.slice(pos1 - pos2) )
                return result.second
            if(pos2 > pos1 and pos2 + len2 >= pos1 + len1):
                ''' 1----XXXXX|
                    2--------|
                The second part of this operation falls within the range of another.
                '''
                result = self.split(pos2 - pos1)
                result.first.recon = self.recon.update(result.first.getLength(), other.what.slice(0, pos1 + len1 - pos2) )
                return result.first
            if(pos2 > pos1 and pos2 + len2 < pos1 + len1):
                '''1-----XXXXXX---|
                   2------|
                Another operation falls completely within the range of this operation. We remove that part.
                '''                
                #We split this operation two times: first at the beginning of the second operation, then at the end of the second operation.
                r1 = self.split(pos2 - pos1)
                r2 = r1.second.split(len2)
                
                #The resulting Delete operation consists of the first and the last part, which are merged back into a single operation.
                result = r1.first.merge(r2.second)
                result.recon = self.recon.update(pos2 - pos1, other.what)
                return result


    def mirror(self):
        '''Mirrors this Delete operation. Returns an operation which inserts the text
        that this Delete operation would remove. If this Delete operation is not
        reversible, the return value is undefined.
        @type Operations.Insert
        '''
        if self.isReversible():
            return Insert(self.position, self.what.copy())


class Split(Operations):
    '''Instantiates a new Split operation object.
    @class An operation which wraps two different operations into a single
    object. This is necessary for example in order to transform a Delete operation 
    against an Insert operation which falls into the range that is to be deleted.
    @param {Operation} first
    @param {Operation} second
    '''
    requiresCID = True
    
    def __init__(self, first, second):
        self.first = first
        self.second = second

    
    def toString(self):
        return 'Split(%s, %s)' % (self.first, self.second)


    def toHTML(self):
        return 'Split(%s, %s)' % (self.first.toHTML(), self.second.toHTML())


    def apply(self, buffer):
        '''Applies the two components of this split operation to the given buffer
        sequentially. The second component is implicitly transformed against the 
        first one in order to do so.
        @param {Buffer} buffer The buffer to which this operation is to be applied.
        '''
        self.first.apply(buffer)
        transformedSecond = self.second.transform(self.first)
        transformedSecond.apply(buffer)


    def cid(self):
        pass
    
    
    def transform(self, other, cid):
        '''Transforms this Split operation against another operation. This is done
        by transforming both components individually.
        @param {Operation} other
        @param {Operation} [cid]
        '''
        if cid == self or cid == other:
            if cid == self:
                return Split(self.first.transform(other, self.first), self.second.transform(other, self.second))
            else:
                return Split(self.first.transform(other, other), self.second.transform(other, other))
        else:
            return Split(self.first.transform(other),self.second.transform(other))


    def mirror(self):        
        '''Mirrors this Split operation. This is done by transforming the second
        component against the first one, then mirroring both components individually.
        @type Operations.Split
        '''
        newSecond = self.second.transform(self.first)
        return Split(self.first.mirror(), newSecond.mirror())


class Recon(object):
    '''Creates a new Recon object.
    @class The Recon class is a helper class which collects the parts of a
    Delete operation that are lost during transformation. This is used to
    reconstruct the text of a remote Delete operation that was issued in a
    previous state, and thus to make such a Delete operation reversible.
    @param {Recon} [recon] Pre-initialize the Recon object with data from another object.
    '''
    def __init__(self, recon = None):
        if(recon != None):
            self.segments = recon.segments.slice(0)
        else:
            self.segments = []

    
    def toString(self):
        return 'Recon(%s)' % self.segments


    def update(self, offset, buffer):
        '''Creates a new Recon object with an additional piece of text to be restored later.
        @param {Number} offset
        @param {Buffer} buffer
        @type {Recon}
        '''
        newRecon = Recon(self)
        if isinstance(buffer,Buffer):            
            newRecon.segments.push(ReconSegment(offset, buffer))
        return newRecon


    def restore(self, buffer):
        '''Restores the recon data in the given buffer.
        @param {Buffer} buffer
        '''
        for segment in self.segments:    
            buffer.splice(segment.offset, 0, segment.buffer)


class ReconSegment(object):
    '''Instantiates a new ReconSegment object.
    @class ReconSegments store a range of text combined with the offset at
    which they are to be inserted upon restoration.
    @param {Number} offset
    @param {Buffer} buffer
    '''
    
    def __init__(self, offset, buffer):
        self.offset = offset
        self.buffer = buffer.copy()


    def toString(self):
        return '(%s,%s)' % (self.offset, self.buffer)


class DoRequest(object):
    '''Initializes a new DoRequest object.
    @class Represents a request made by an user at a certain time.
    @param {Number} user The user that issued the request
    @param {Vector} vector The time at which the request was issued
    @param {Operation} operation
    '''
    def __init__(self, user, vector, operation):
        self.user = user
        self.vector = vector
        self.operation = operation
        

    def toString(self):
        return 'DoRequest(%s, %s, %s)' % (self.user, self.vector, self.operation)
        

    def toHTML(self):
        return 'DoRequest(%s, %s, %s)' % (self.user, self.vector.toHTML(), self.operation.toHTML())
        

    def copy(self):
        return DoRequest(self.user, self.vector, self.operation)
        

    def execute(self, state):
        '''Applies the request to a State.
        @param {State} state The state to which the request should be applied.
        '''
        self.operation.apply(state.buffer)
        state.vector = state.vector.incr(self.user, 1)
        return self
        

    def transform(self, other, cid):
        '''Transforms this request against another request.
        @param {DoRequest} other
        @param {DoRequest} [cid] The concurrency ID of the two requests. This is
        the request that is to be transformed in case of conflicting operations.
        @type DoRequest
        '''
        if isinstance(self.operation, NoOp):
            newOperation = NoOp()
        else:            
            if(cid == self):
                op_cid = self.operation
            if(cid == other):
                op_cid = other.operation
        
            newOperation = self.operation.transform(other.operation, op_cid)
        return DoRequest(self.user, self.vector.incr(other.user), newOperation)


    def mirror(self, amount):        
        '''Mirrors the request. This inverts the operation and increases the issuer's
        component of the request time by the given amount.
        @param {Number} [amount] The amount by which the request time is
        increased. Defaults to 1.
        @type DoRequest
        '''
        try: amount = int(source)
        except: amount = 1
        return DoRequest(self.user, self.vector.incr(self.user, amount), self.operation.mirror())


    def fold(self, user, amount):
        '''Folds the request along another user's axis. This increases that user's
        component by the given amount, which must be a multiple of 2.
        @type DoRequest
        '''
        if(amount % 2 == 1):
            raise 'Fold amounts must be multiples of 2.'
        return DoRequest(self.user, self.vector.incr(user, amount), self.operation)


    def makeReversible(self, translated, state):
        '''Makes a request reversible, given a translated version of this request
        and a State object. This only applies to requests carrying a Delete
        operation; for all others, this does nothing.
        @param {DoRequest} translated This request translated to the given state
        @param {State} state The state which is used to make the request
        reversible.
        @type DoRequest
        '''
        result = self.copy()    
        if isinstance(self.operation, Operations.Delete):
            result.operation = self.operation.makeReversible(translated.operation, state)
        return result


class UndoRequest(object): 
    '''Instantiates a new undo request.
    @class Represents an undo request made by an user at a certain time.
    @param {Number} user
    @param {Vector} vector The time at which the request was issued.
    '''
    def __init__(self, user, vector):
        self.user = user
        self.vector = vector


    def toString(self):
        return 'UndoRequest(%s, %s)' % (self.user, self.vector)

    def toHTML(self):
        return 'UndoRequest(%s, %s)' % (self.user, self.vector.toHTML())

    def copy(self):
        return UndoRequest(self.user, self.vector)

    def associatedRequest(self, log):
        '''Finds the corresponding DoRequest to this UndoRequest.
        @param {Array} log The log to search
        @type DoRequest
        '''
        sequence = 1
        index = log.index(self)       
        if(index == -1): index = log.length - 1
    
        while index >= 0:
            # === => ==
            if log[index] == self or log[index].user != self.user:
                continue
            if log[index].vector.get(self.user) > self.vector.get(self.user):
                continue        
            if isinstance(log[index], UndoRequest):
                sequence += 1;
            else:
                sequence -= 1;        
            if(sequence == 0):
                return log[index]
            index = index - 1


class RedoRequest(object):
    '''Instantiates a new redo request.
    @class Represents an redo request made by an user at a certain time.
    @param {Number} user
    @param {Vector} vector The time at which the request was issued.
    '''
    def __init__(self, user, vector):
        self.user = user
        self.vector = vector        

    def toString(self):        
        return 'RedoRequest(%s, %s)' % (self.user, self.vector)

    def toHTML(self):        
        return 'RedoRequest(%s, %s)' % (self.user, self.vector.toHTML())

    def copy(self):
        return RedoRequest(self.user, self.vector)
        
    def associatedRequest(self, log):
        '''Finds the corresponding UndoRequest to this RedoRequest.
        @param {Array} log The log to search
        @type UndoRequest
        '''
        sequence = 1
        index = log.index(self)        
        if(index == -1): index = log.length - 1
    
        while index >= 0:
            # === => ==
            if log[index] == self or log[index].user != self.user: continue
            if log[index].vector.get(self.user) > self.vector.get(self.user): continue       
            if isinstance(log[index], RedoRequest): sequence += 1
            else: sequence -= 1            
            if(sequence == 0):
                return log[index]
     

class Vector(object):
    '''@class Stores state vectors.
    @param [value] Pre-initialize the vector with existing values. This can be
    a Vector object, a generic Object with numeric properties, or a string of the form "1:2;3:4;5:6".
    '''
    user_regex = u'/\d+/'
    timestring_regex = u'/(\d+):(\d+)/g'
    users = []
    
    def __init__(self, value = None):
        #check if value is a vector object
        if type(value).__name__ == "object":
            for user in value:
                if re.match(user, Vector.user_regex) and value[user] > 0:
                    self.user = value[user]
                    
        elif isinstance(value, str):
            #exec => match
            match = re.match(value, self.timestring_regex)
            #match = self.timestring_regex.match(value)
            while match != None:
                self.users[match.group(1)] = int(match.group(2))
                #exec => match
                match = Vector.timestring_regex.match(value)
                

    def eachUser(self, callback):
        '''Helper function to easily iterate over all users in this vector.
        @param {function} callback Callback function which is called with the user
        and the value of each component. If this callback function returns false,
        iteration is stopped at that point and false is returned.
        @type Boolean
        @returns True if the callback function has never returned false; returns False otherwise.
        '''
        for user in self.users:
            print 'bla'
            print user
            if user.match(Vector.user_regex):
                if callback(int(user), self[user]) == False:
                    return False   


    def toString(self):            
        '''Returns this vector as a string of the form "1:2;3:4;5:6"
        @type String
        '''
        components = []
        def Func(u, v):
            print "Foo"            
            print u
            if(v > 0):
                components.append(u+":"+v)    
        self.eachUser(Func)
        components.sort()   
        return ';'.join(components)

    def toHTML():
        return self.toString()        
        
    def add(self, other):
        '''Returns the sum of two vectors.
        @param {Vector} other
        '''
        def Func(u, v):
            result[u] = result.get(u) + v
        result = Vector(self)    
        other.eachUser(Func)
        result[u] = result.get(u) + v
        return result;

    def copy(self): 
        '''Returns a copy of this vector.'''
        return Vector(self)


    def get(self, user):
        '''Returns a specific component of this vector, or 0 if it is not defined.
        @param {Number} user Index of the component to be returned
        '''
        if self.user != None:
            return self.user
        else:
            return 0

    def causallyBefore(self, other):
        '''Calculates whether this vector is smaller than or equal to another vector.
        This means that all components of this vector are less than or equal to
        their corresponding components in the other vector.
        @param {Vector} other The vector to compare to
        @type Boolean
        '''
        def Func(u, v):
            return v <= other.get(u)
        return self.eachUser(Func)


    def equals(self, other):
        '''Determines whether this vector is equal to another vector. This is true if
        all components of this vector are present in the other vector and match
        their values, and vice-versa.
        @param {Vector} other The vector to compare to
        @type Boolean
        '''
        def Func1(u, v):
            return other.get(u) == v        
        eq1 = self.eachUser(Func)    
        this = self
        def Func2(u, v):
            return this.get(u) == v
        eq2 = other.eachUser(Func2)
        return eq1 and eq2


    def incr(self, user, by):
        '''Returns a new vector with a specific component increased by a given
        amount.
        @param {Number} user Component to increase
        @param {Number} [by] Amount by which to increase the component (default 1)
        @type Vector
        '''
        result = Vector(self)    
        if by == undefined:
            by = 1    
        result[user] = result.get(user) + by
        return result;

    def leastCommonSuccessor(self, v1, v2):
        '''Calculates the least common successor of two vectors.
        @param {Vector} v1
        @param {Vector} v2
        @type Vector
        '''
        result = v1.copy()  
        def Func(u, v):
            val1 = v1.get(u)
            val2 = v2.get(u)
            if val1 < val2:
                result[u] = val2
            else:
                #result[u] = val1
                pass
        v2.eachUser(Func)    
        return result


class State(object):
    '''Instantiates a new state object.
    @class Stores and manipulates the state of a document by keeping track of
    its state vector, content and history of executed requests.
    @param {Buffer} [buffer] Pre-initialize the buffer
    @param {Vector} [vector] Set the initial state vector
    '''
    def __init__(self, buffer = None, vector = None):
        if isinstance(buffer, Buffer):
            self.buffer = buffer.copy()
        else:
            self.buffer = Buffer()    
        self.vector = Vector(vector)
        self.request_queue = []
        self.log = []
        self.cache = {}
        
    def translate(self, request, targetVector, noCache):
        '''Translates a request to the given state vector.
        @param {Request} request The request to translate
        @param {Vector} targetVector The target state vector
        @param {Boolean} [nocache] Set to true to bypass the translation cache.
        '''
        if isinstance(request, DoRequest) and request.vector.equals(targetVector):
            #If the request vector is not an undo/redo request and is already at the desired state, 
            #simply return the original request since there is nothing to do.
            return request.copy()

        #Before we attempt to translate the request, we check whether it is cached already.
        cache_key = [request, targetVector].toString()
        if self.cache != None and not noCache:            
            if not self.cache[cache_key]:
                self.cache[cache_key] = self.translate(request, targetVector, true)        
        #FIXME: translated requests are not cleared from the cache, so this might fill up considerably.
        return self.cache[cache_key]

        if isinstance(request, UndoRequest) or isinstance(request, RedoRequest):
            '''If we're dealing with an undo or redo request, we first try to see
            whether a late mirror is possible. For this, we retrieve the
            associated request to this undo/redo and see whether it can be
            translated and then mirrored to the desired state.
            '''
            assocReq = request.associatedRequest(self.log)        
            '''The state we're trying to mirror at corresponds to the target
            vector, except the component of the issuing user is changed to
            match the one from the associated request.
            '''
            mirrorAt = targetVector.copy()
            mirrorAt[request.user] = assocReq.vector.get(request.user)        
            if self.reachable(mirrorAt):
                translated = self.translate(assocReq, mirrorAt)
                mirrorBy = targetVector.get(request.user) - mirrorAt.get(request.user)            
                mirrored = translated.mirror(mirrorBy)
                return mirrored        
            #If mirrorAt is not reachable, we need to mirror earlier and then
            #perform a translation afterwards, which is attempted next.
        for _user in self.vector:
            #We now iterate through all users to see how we can translate the request to the desired state.
            if not _user.match(Vector.user_regex): continue        
            user = int(_user)        
            #The request's issuing user is left out since it is not possible to transform or fold a request along its own user
            if user == request.user: continue        
            #We can only transform against requests that have been issued
            #between the translated request's vector and the target vector.
            if targetVector.get(user) <= request.vector.get(user): continue
            
            #Fetch the last request by this user that contributed to the current state vector.
            lastRequest = self.requestByUser(user, targetVector.get(user) - 1)        
            if isinstance(lastRequest, UndoRequest) or isinstance(lastRequest, RedoRequest):
                #When the last request was an undo/redo request, we can try to
                #"fold" over it. By just skipping the do/undo or undo/redo pair,
                #we pretend that nothing has changed and increase the state vector.             
                foldBy = targetVector.get(user) - lastRequest.associatedRequest(self.log).vector.get(user)            
                if(targetVector.get(user) >= foldBy):
                    foldAt = targetVector.incr(user, -foldBy)                
                    #We need to make sure that the state we're trying to fold at is reachable and that the request 
                    #we're translating was issued before it.                
                    if self.reachable(foldAt) and request.vector.causallyBefore(foldAt):
                        translated = self.translate(request, foldAt)
                        folded = translated.fold(user, foldBy)                    
                        return folded
            #If folding and mirroring is not possible, we can transform this
            #request against other users' requests that have contributed to
            #the current state vector.        
            transformAt = targetVector.incr(user, -1)
            if transformAt.get(user) >= 0 and self.reachable(transformAt):
                lastRequest = self.requestByUser(user, transformAt.get(user))            
                r1 = self.translate(request, transformAt)
                r2 = self.translate(lastRequest, transformAt)            
                if r1.operation.requiresCID:
                    #For the Insert operation, we need to check whether it is
                    #possible to determine which operation is to be transformed.
                    cid = r1.operation.cid(r2.operation)            
                    if not cid:
                        #When two requests insert text at the same position,
                        #the transformation result is undefined. We therefore
                        #need to perform some tricks to decide which request
                        #has to be transformed against which.
                        
                        #The first try is to transform both requests to a
                        #common successor before the transformation vector.
                        lcs = Vector.leastCommonSuccessor(request.vector, lastRequest.vector)                    
                        if self.reachable(lcs):
                            r1t = self.translate(request, lcs)
                            r2t = self.translate(lastRequest, lcs)
                            #We try to determine the CID at this vector, which
                            #hopefully yields a result.
                            cidt = r1t.operation.cid(r2t.operation)                        
                            if cidt == r1t.operation:
                                cid = r1.operation
                            elif cidt == r2t.operation:
                                cid = r2.operation
                        if not cid:                        
                            #If we arrived here, we couldn't decide for a CID,
                            #so we take the last resort: use the user ID of the
                            #requests to decide which request is to be
                            #transformed. This behavior is specified in the
                            #Infinote protocol.                        
                            if r1.user < r2.user:
                                cid = r1.operation
                            if r1.user > r2.user:
                                cid = r2.operation                
                    if cid == r1.operation:
                        cid_req = r1
                    if cid == r2.operation:
                        cid_req = r2            
                return r1.transform(r2, cid_req)
        raise 'Could not find a translation path'


    def queue(self, request):
        '''Adds a request to the request queue.
        @param {Request} request The request to be queued.
        '''
        self.request_queue.append(request)
        

    def canExecute(self, request = None): 
        '''Checks whether a given request can be executed in the current state.
        @type Boolean
        '''
        if request == None: return False
    
        if isinstance(request, UndoRequest) or isinstance(request, RedoRequest):
            return request.associatedRequest(self.log) != None
        else:
            return request.vector.causallyBefore(self.vector)
            

    def execute(self, request = None):        
        '''Executes a request that is executable.
        @param {Request} [request] The request to be executed. If omitted, an
        executable request is picked from the request queue instead.
        @returns The request that has been executed, or None if no request
        has been executed.
        '''
        if request == None:
            #Pick an executable request from the queue.
            #for (index = 0 ++ loop)
            for index, value in enumerate(self.request_queue):
                request = self.request_queue[index]
                if self.canExecute(request):
                    print 'bla'
                    self.request_queue.splice(index, 1)
                    break

        if not self.canExecute(request):
            #Not executable yet - put it (back) in the queue.
            if request != None:
                self.queue(request)        
            return
    
        request = request.copy()
    
        if isinstance(request, UndoRequest) or isinstance(request, RedoRequest):
            #For undo and redo requests, we change their vector to the vector
            #of the original request, but leave the issuing user's component untouched.
            assocReq = request.associatedRequest(self.log)
            newVector = Vector(assocReq.vector)
            newVector[request.user] = request.vector.get(request.user)
            request.vector = newVector
    
        translated = self.translate(request, self.vector)
    
        if isinstance(request, DoRequest) and isinstance(request.operation, Delete):
            #Since each request might have to be mirrored at some point, it
            #needs to be reversible. Delete requests are not reversible by
            #default, but we can make them reversible.
            self.log.append(request.makeReversible(translated, self))
        else:
            self.log.append(request);
    
        translated.execute(self)
    
        if self.onexecute:
            self.onexecute(translated)
    
        return translated

    
    def executeAll(self):
        '''Executes all queued requests that are ready for execution.'''    
        while executed:
            executed = self.execute()
            
    
    def reachable(self, vector):
        '''Determines whether a given state is reachable by translation.
        @param {Vector} vector
        @type Boolean
        '''
        this = self
        def Func(u, v):
            return self.reachableUser(vector, u)
        return this.vector.eachUser(Func)


    def reachableUser(self, vector, user):
        n = vector.get(user)    
        while True:
            if n == 0:
                return true
        
            r = self.requestByUser(user, n - 1)        
        if r == None:
            return false
        if isinstance(r, DoRequest):
            w = r.vector
            return w.causallyBefore(vector)
        else:
            assocReq = r.associatedRequest(self.log)
            n = assocReq.vector.get(user)


    def requestByUser(self, user, getIndex):
        '''Retrieve an user's request by its index.
        @param {Number} user
        @param {Number} index The number of the request to be returned
        '''
        userReqCount = 0;
        for reqIndex in self.log:
            if self.log[reqIndex].user == user:
                if(userReqCount == getIndex):
                    return self.log[reqIndex]
                else: userReqCount += 1


class Segment(object):
    '''Creates a new Segment instance given a user ID and a string.
    @param {Number} user User ID
    @param {String} text Text
    @class Stores a chunk of text together with the user it was written by.
    '''
    def __init__(self, user, text):
        self.user = user
        self.text = text
        

    def toString(self):
        return self.text


    def toHTML(self):
        text = self.text.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
        return '<span class="segment user-' + self.user + '">' + text + '</span>'


    def copy(self):
        '''Creates a copy of this segment.
        @returns {Segment} A copy of this segment.
        '''
        return Segment(self.user, self.text)


class Buffer(object):
    '''
    Creates a new Buffer instance from the given array of
    segments.
    @param {Array} [segments] The segments that this buffer should be
    pre-filled with.
    @class Holds multiple Segments and provides methods for modifying them at a character level.
    '''
    def __init__(self, segments = None):
        self.segments = []    
        if segments != None:
            for segment in segments:
                self.segments.append(segment.copy())


    def toString(self):
        output = ''
        for segment in self.segments:
            output +=segment.toString()
        return output


    def toHTML(self):
        result = '<span class="buffer">'
        #for index ++ loop
        for index in enumerate(self.segments):
            result += self.segments[index].toHTML()
        result += '</span>'
        return result


    def copy(self):
        '''Creates a deep copy of this buffer.
        @type Buffer
        '''
        return self.slice(0)


    def compact(self):
        '''Cleans up the buffer by removing empty segments and combining adjacent
        segments by the same user.
        '''
        segmentIndex = 0;
        while segmentIndex < len(self.segments):
            if len(self.segments[segmentIndex].text) == 0:
                #This segment is empty, remove it.
                self.segments.splice(segmentIndex, 1)
                continue
            elif segmentIndex < len(self.segments) - 1 and self.segments[segmentIndex].user == self.segments[segmentIndex+1].user:
                #Two consecutive segments are from the same user; merge them into one.
                self.segments[segmentIndex].text += self.segments[segmentIndex+1].text                
                self.segments.splice(segmentIndex+1, 1)
                continue            
            segmentIndex += 1;


    def getLength(self):
        '''Calculates the total number of characters contained in this buffer.
        @returns Total character count in this buffer
        @type Number
        '''
        length = 0;
        # for index++ loop
        for index in self.segments:
            length += self.segments[index].text.length
    
        return length


    def slice(self, begin, end = None):
        '''Extracts a deep copy of a range of characters in this buffer and returns
        it as a new Buffer object.
        @param {Number} begin Index of first character to return
        @param {Number} [end] Index of last character (exclusive). If not
        provided, defaults to the total length of the buffer.
        @returns New buffer containing the specified character range.
        @type Buffer
        '''
        result = Buffer()    
        segmentIndex = 0
        segmentOffset = 0
        sliceBegin = begin
        sliceEnd = end    
        if sliceEnd == None:
            sliceEnd = sys.maxint 
        while segmentIndex < len(self.segments) and sliceEnd >= segmentOffset:
            segment = self.segments[segmentIndex]
            if sliceBegin - segmentOffset < len(segment.text) and sliceEnd - segmentOffset > 0:
                #segment.text.slice => self.slice
                newText = segment.text[sliceBegin - segmentOffset:sliceEnd - segmentOffset]
                newSegment = Segment(segment.user, newText)
                result.segments.append(newSegment)                
                sliceBegin += len(newText)
            segmentOffset += len(segment.text)
            segmentIndex += 1
        result.compact()
        return result


    def splice(self, index, remove, insert):
        '''Like the Array "splice" method, this method allows for removing and
        inserting text in a buffer at a character level.
        @param {Number} index    The offset at which to begin inserting/removing
        @param {Number} [remove] Number of characters to remove
        @param {Buffer} [insert] Buffer to insert
        '''
        if index > self.getLength():
            raise 'Buffer splice operation out of bounds'
    
        segmentIndex = 0
        segmentOffset = 0
        spliceIndex = index
        spliceCount = remove
        spliceInsertOffset = None
        while segmentIndex < self.segments.length:
            segment = self.segments[segmentIndex]            
            if spliceIndex >= 0 and spliceIndex < segment.text.length:
                #This segment is part of the region to splice.                
                #Store the text that this splice operation removes to adjust the
                #splice offset correctly later on.
                removedText = segment.text.slice(spliceIndex, spliceIndex + spliceCount)                
                if spliceIndex == 0:
                    #abcdefg
                    #  ^        We're splicing at the beginning of a segment                    
                    if spliceIndex + spliceCount < segment.text.length:
                        #abcdefg
                        #^---^    Remove a part at the beginning                        
                        if spliceInsertOffset == undefined:
                            spliceInsertOffset = segmentIndex
                            
                        segment.text = segment.text.slice(spliceIndex + spliceCount)
                    else:
                        #abcdefg
                        #^-----^  Remove the entire segment                        
                        if spliceInsertOffset == undefined:
                            spliceInsertOffset = segmentIndex                        
                        segment.text = ""
                        self.segments.splice(segmentIndex, 1)
                        segmentIndex -= 1
                else:
                    #abcdefg
                    #  ^      We're splicing inside a segment                
                    if spliceInsertOffset == undefined:
                        spliceInsertOffset = segmentIndex + 1
                    
                    if spliceIndex + spliceCount < segment.text.length:
                        # abcdefg
                        #   ^--^   Remove a part in between
                        
                        # Note that if spliceCount == 0, this function only
                        # splits the segment in two. This is necessary in case we
                        # want to insert new segments later.                        
                        splicePost = Segment(segment.user, segment.text.slice(spliceIndex + spliceCount))
                        segment.text = segment.text.slice(0, spliceIndex)
                        self.segments.splice(segmentIndex + 1, 0, splicePost)
                    else:
                        # abcdefg
                        #   ^---^  Remove a part at the end                            
                        segment.text = segment.text.slice(0, spliceIndex)
                spliceCount -= removedText.length
            
            if spliceIndex < segment.text.length and spliceCount == 0:
                #We have removed the specified amount of characters. No need to
                #continue this loop since nothing remains to be done.                
                if spliceInsertOffset == None:
                    spliceInsertOffset = spliceIndex                
                break            
            spliceIndex -= segment.text.length            
            segmentIndex += 1
        if isinstance(insert, Buffer):
            #If a buffer has been given, we insert copies of its segments at the specified position.            
            if spliceInsertOffset == None:
                spliceInsertOffset = self.segments.length      
            #for insertIndex++ loop
            for insertIndex in insert.segments:
                self.segments.splice(spliceInsertOffset + insertIndex, 0, insert.segments[insertIndex].copy())        
        #Clean up since the splice operation might have fragmented some segments.
        self.compact()